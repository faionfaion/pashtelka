"""Tests for pipeline orchestrator: modes (generate, publish, digest) and CLI.

After refactoring, the code is split across:
  - pipeline.modes.generate — batch generation
  - pipeline.modes.publish — mechanical TG publish
  - pipeline.modes.digest — evening digest
  - pipeline.cli — CLI entry point
  - pipeline.main — backward-compatible re-exports
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from pipeline.context import PipelineContext


# ========== pipeline.main re-exports ==========

class TestMainReexports:
    """pipeline.main should re-export everything for backward compatibility."""

    def test_exports_cli(self):
        from pipeline.main import cli
        assert callable(cli)

    def test_exports_run_generate(self):
        from pipeline.main import run_generate
        assert callable(run_generate)

    def test_exports_run_publish(self):
        from pipeline.main import run_publish
        assert callable(run_publish)

    def test_exports_run_digest(self):
        from pipeline.main import run_digest
        assert callable(run_digest)


# ========== pipeline.modes.generate ==========

class TestReviewLoop:
    """_review_loop: article review cycle."""

    @patch("pipeline.modes.generate.s5_revise")
    @patch("pipeline.modes.generate.s4_review")
    def test_approved_after_one_revision(self, mock_review, mock_revise):
        """Approves on second review (after 1 revision, cycle >= 1)."""
        ctx = PipelineContext()

        call_count = [0]
        def review_side_effect(c):
            call_count[0] += 1
            if call_count[0] >= 2:
                c.review_approved = True

        mock_review.run.side_effect = review_side_effect

        from pipeline.modes.generate import _review_loop
        _review_loop(ctx)
        assert ctx.review_approved is True
        assert mock_revise.run.call_count >= 1

    @patch("pipeline.modes.generate.s5_revise")
    @patch("pipeline.modes.generate.s4_review")
    def test_max_cycles_reached(self, mock_review, mock_revise):
        """When max cycles reached, loop exits without approval."""
        ctx = PipelineContext()
        mock_review.run.side_effect = lambda c: None  # Never approves

        from pipeline.modes.generate import _review_loop
        from pipeline.config import MAX_REVIEW_CYCLES
        _review_loop(ctx)
        assert mock_review.run.call_count == MAX_REVIEW_CYCLES

    @patch("pipeline.modes.generate.s5_revise")
    @patch("pipeline.modes.generate.s4_review")
    def test_always_does_at_least_one_revision(self, mock_review, mock_revise):
        """Even if approved on first review, must do at least 1 revision (cycle >= 1 check)."""
        ctx = PipelineContext()

        def review_first_approve(c):
            c.review_approved = True

        mock_review.run.side_effect = review_first_approve

        from pipeline.modes.generate import _review_loop
        _review_loop(ctx)
        # First cycle: review approves, but cycle=0 so cycle>=1 is False, so revise runs
        assert mock_revise.run.call_count >= 1


class TestLoadWrittenTopics:
    """_load_written_topics: load set of already-written topic labels."""

    @patch("pipeline.modes.generate.STATE_DIR")
    def test_no_file(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        (tmp_path / "plans").mkdir(parents=True)

        from pipeline.modes.generate import _load_written_topics
        result = _load_written_topics({"date": "2026-04-09"})
        assert result == set()

    @patch("pipeline.modes.generate.STATE_DIR")
    def test_existing_file(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir(parents=True)
        (plans_dir / "2026-04-09_written.json").write_text('["Topic A", "Topic B"]', encoding="utf-8")

        from pipeline.modes.generate import _load_written_topics
        result = _load_written_topics({"date": "2026-04-09"})
        assert result == {"Topic A", "Topic B"}


class TestMarkTopicWritten:
    """_mark_topic_written: mark a topic as written."""

    @patch("pipeline.modes.generate.STATE_DIR")
    def test_mark_new_topic(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        (tmp_path / "plans").mkdir(parents=True)

        from pipeline.modes.generate import _mark_topic_written
        _mark_topic_written({"date": "2026-04-09"}, "Topic A")

        written_file = tmp_path / "plans" / "2026-04-09_written.json"
        assert written_file.exists()
        written = json.loads(written_file.read_text(encoding="utf-8"))
        assert "Topic A" in written

    @patch("pipeline.modes.generate.STATE_DIR")
    def test_append_to_existing(self, mock_state, tmp_path):
        mock_state.__truediv__ = lambda self, x: tmp_path / x
        plans_dir = tmp_path / "plans"
        plans_dir.mkdir(parents=True)
        (plans_dir / "2026-04-09_written.json").write_text('["Topic A"]', encoding="utf-8")

        from pipeline.modes.generate import _mark_topic_written
        _mark_topic_written({"date": "2026-04-09"}, "Topic B")

        written = json.loads((plans_dir / "2026-04-09_written.json").read_text(encoding="utf-8"))
        assert "Topic A" in written
        assert "Topic B" in written


class TestGenerateOneArticle:
    """_generate_one_article: generate a single article for one editorial topic."""

    @patch("pipeline.modes.generate.s6_generate_tg")
    @patch("pipeline.modes.generate.s4_review")
    @patch("pipeline.modes.generate.s5_revise")
    @patch("pipeline.modes.generate.s3_generate")
    @patch("pipeline.modes.generate.s2_research")
    @patch("pipeline.modes.generate.s7_save")
    def test_successful_generation(self, mock_save, mock_research, mock_generate, mock_revise, mock_review, mock_tg):
        from pipeline.run_report import RunReport
        report = RunReport()

        # Configure mocks for review loop to approve quickly
        def review_approve(c):
            c.review_approved = True
        mock_review.run.side_effect = review_approve

        def generate_fill(c):
            c.slug = "generated-slug"
            c.title = "Generated Title"
        mock_generate.run.side_effect = generate_fill

        topic = {"topic": "Test topic", "type": "news", "priority": 1}

        from pipeline.modes.generate import _generate_one_article
        result = _generate_one_article(
            topic=topic,
            rss_items=[],
            posted_slugs=[],
            report=report,
            dry_run=True,
        )
        assert result is not None
        assert result.slot_type == "news"
        mock_research.run.assert_called_once()

    @patch("pipeline.modes.generate.s2_research")
    def test_generation_failure_returns_none(self, mock_research):
        from pipeline.run_report import RunReport
        report = RunReport()
        mock_research.run.side_effect = Exception("Research failed")

        topic = {"topic": "Failing topic", "type": "news", "priority": 1}

        from pipeline.modes.generate import _generate_one_article
        result = _generate_one_article(
            topic=topic,
            rss_items=[],
            posted_slugs=[],
            report=report,
        )
        assert result is None


class TestRunGenerate:
    """modes.generate.run: batch all articles for the day."""

    @patch("pipeline.modes.generate.s8_verify")
    @patch("pipeline.modes.generate.s7_deploy")
    @patch("pipeline.modes.generate._generate_one_article")
    @patch("pipeline.modes.generate._load_written_topics")
    @patch("pipeline.modes.generate.s1_collect")
    @patch("pipeline.modes.generate.s0_editorial_plan")
    def test_full_generate_flow(self, mock_s0, mock_s1, mock_written, mock_gen, mock_deploy, mock_verify, tmp_path):
        mock_s0.run.return_value = {
            "date": "2026-04-09",
            "articles": [{"topic": "Topic A", "type": "news"}],
        }
        mock_s1.collect_context.return_value = ([], [])
        mock_written.return_value = set()

        ctx = PipelineContext()
        ctx.slug = "topic-a"
        ctx.title = "Topic A"
        ctx.image_path = None
        mock_gen.return_value = ctx

        with patch("pipeline.modes.generate._mark_topic_written"):
            with patch("pipeline.modes.generate.RunReport") as MockReport:
                mock_report_inst = MagicMock()
                mock_report_inst.save.return_value = tmp_path / "report.json"
                MockReport.return_value = mock_report_inst

                from pipeline.modes.generate import run
                completed = run(dry_run=True)
                assert len(completed) == 1

    @patch("pipeline.modes.generate.s1_collect")
    @patch("pipeline.modes.generate.s0_editorial_plan")
    def test_generate_skips_written_topics(self, mock_s0, mock_s1, tmp_path):
        mock_s0.run.return_value = {
            "date": "2026-04-09",
            "articles": [
                {"topic": "Already Written", "type": "news"},
                {"topic": "New Topic", "type": "news"},
            ],
        }
        mock_s1.collect_context.return_value = ([], [])

        with patch("pipeline.modes.generate._load_written_topics", return_value={"Already Written"}):
            with patch("pipeline.modes.generate._generate_one_article") as mock_gen:
                ctx = PipelineContext()
                ctx.slug = "new-topic"
                ctx.image_path = None
                mock_gen.return_value = ctx

                with patch("pipeline.modes.generate._mark_topic_written"):
                    with patch("pipeline.modes.generate.RunReport") as MockReport:
                        mock_report_inst = MagicMock()
                        mock_report_inst.save.return_value = tmp_path / "r.json"
                        MockReport.return_value = mock_report_inst

                        from pipeline.modes.generate import run
                        completed = run(dry_run=True)
                        # Only "New Topic" should be generated
                        assert mock_gen.call_count == 1

    @patch("pipeline.modes.generate.s8_verify")
    @patch("pipeline.modes.generate.s7_deploy")
    @patch("pipeline.modes.generate._generate_one_article")
    @patch("pipeline.modes.generate._load_written_topics")
    @patch("pipeline.modes.generate.s1_collect")
    @patch("pipeline.modes.generate.s0_editorial_plan")
    def test_generate_with_deploy(self, mock_s0, mock_s1, mock_written, mock_gen, mock_deploy, mock_verify, tmp_path):
        """Test the deploy path (non-dry-run) with completed articles."""
        mock_s0.run.return_value = {
            "date": "2026-04-09",
            "articles": [{"topic": "Topic A", "type": "news"}],
        }
        mock_s1.collect_context.return_value = ([], [])
        mock_written.return_value = set()

        ctx = PipelineContext()
        ctx.slug = "topic-a"
        ctx.title = "Topic A"
        ctx.image_path = Path("/tmp/img.jpg")
        mock_gen.return_value = ctx

        with patch("pipeline.modes.generate._mark_topic_written"):
            with patch("pipeline.modes.generate.RunReport") as MockReport:
                mock_report_inst = MagicMock()
                mock_report_inst.save.return_value = tmp_path / "report.json"
                MockReport.return_value = mock_report_inst

                from pipeline.modes.generate import run
                completed = run(dry_run=False)
                assert len(completed) == 1
                mock_deploy.run.assert_called_once()
                mock_verify.run.assert_called_once()

    @patch("pipeline.modes.generate._generate_one_article")
    @patch("pipeline.modes.generate._load_written_topics")
    @patch("pipeline.modes.generate.s1_collect")
    @patch("pipeline.modes.generate.s0_editorial_plan")
    def test_generate_all_fail(self, mock_s0, mock_s1, mock_written, mock_gen, tmp_path):
        """When all articles fail, report saves with 'empty' status."""
        mock_s0.run.return_value = {
            "date": "2026-04-09",
            "articles": [{"topic": "Failing", "type": "news"}],
        }
        mock_s1.collect_context.return_value = ([], [])
        mock_written.return_value = set()
        mock_gen.return_value = None

        with patch("pipeline.modes.generate._mark_topic_written"):
            with patch("pipeline.modes.generate.RunReport") as MockReport:
                mock_report_inst = MagicMock()
                mock_report_inst.save.return_value = tmp_path / "report.json"
                MockReport.return_value = mock_report_inst

                from pipeline.modes.generate import run
                completed = run(dry_run=True)
                assert len(completed) == 0
                mock_report_inst.finish.assert_called_with("empty")

    @patch("pipeline.modes.generate._generate_one_article")
    @patch("pipeline.modes.generate._load_written_topics")
    @patch("pipeline.modes.generate.s1_collect")
    @patch("pipeline.modes.generate.s0_editorial_plan")
    def test_generate_report_save_failure(self, mock_s0, mock_s1, mock_written, mock_gen, tmp_path):
        """Report save failure should not crash."""
        mock_s0.run.return_value = {
            "date": "2026-04-09",
            "articles": [{"topic": "Topic A", "type": "news"}],
        }
        mock_s1.collect_context.return_value = ([], [])
        mock_written.return_value = set()
        ctx = PipelineContext()
        ctx.slug = "topic-a"
        ctx.image_path = None
        mock_gen.return_value = ctx

        with patch("pipeline.modes.generate._mark_topic_written"):
            with patch("pipeline.modes.generate.RunReport") as MockReport:
                mock_report_inst = MagicMock()
                mock_report_inst.save.side_effect = Exception("Save failed")
                MockReport.return_value = mock_report_inst

                from pipeline.modes.generate import run
                completed = run(dry_run=True)
                assert len(completed) == 1


# ========== pipeline.modes.publish ==========

class TestRunPublish:
    """modes.publish.run: pick best article, send to TG."""

    @patch("pipeline.modes.publish.s10_pick_and_publish")
    def test_publish_success(self, mock_s10):
        mock_s10.run.return_value = {"slug": "test", "msg_id": 123}

        from pipeline.modes.publish import run
        result = run()
        assert result["slug"] == "test"

    @patch("pipeline.modes.publish.s10_pick_and_publish")
    def test_publish_nothing(self, mock_s10):
        mock_s10.run.return_value = None

        from pipeline.modes.publish import run
        result = run()
        assert result is None


# ========== pipeline.modes.digest ==========

class TestRunDigest:
    """modes.digest.run: compile day's articles, send to TG."""

    @patch("pipeline.modes.digest.s11_digest")
    def test_digest_success(self, mock_s11):
        mock_s11.run.return_value = {"msg_id": 789, "article_count": 5}

        from pipeline.modes.digest import run
        result = run()
        assert result["msg_id"] == 789

    @patch("pipeline.modes.digest.s11_digest")
    def test_digest_skipped(self, mock_s11):
        mock_s11.run.return_value = None

        from pipeline.modes.digest import run
        result = run()
        assert result is None


# ========== pipeline.cli ==========

class TestCli:
    """cli: CLI entry point."""

    @patch("pipeline.cli.sys.exit")
    @patch("pipeline.cli.argparse.ArgumentParser.parse_args")
    def test_cli_generate_mode(self, mock_args, mock_exit):
        mock_args.return_value = MagicMock(mode="generate", dry_run=False, verbose=False)

        with patch("pipeline.modes.generate.run", return_value=[]) as mock_gen:
            from pipeline.cli import cli
            cli()
            mock_gen.assert_called_once_with(dry_run=False)

    @patch("pipeline.cli.sys.exit")
    @patch("pipeline.cli.argparse.ArgumentParser.parse_args")
    def test_cli_publish_mode(self, mock_args, mock_exit):
        mock_args.return_value = MagicMock(mode="publish", dry_run=False, verbose=False)

        with patch("pipeline.modes.publish.run", return_value={"slug": "test", "msg_id": 1}) as mock_pub:
            from pipeline.cli import cli
            cli()
            mock_pub.assert_called_once()

    @patch("pipeline.cli.sys.exit")
    @patch("pipeline.cli.argparse.ArgumentParser.parse_args")
    def test_cli_digest_mode(self, mock_args, mock_exit):
        mock_args.return_value = MagicMock(mode="digest", dry_run=False, verbose=False)

        with patch("pipeline.modes.digest.run", return_value={"msg_id": 1, "article_count": 5}) as mock_dig:
            from pipeline.cli import cli
            cli()
            mock_dig.assert_called_once()

    @patch("pipeline.cli.sys.exit")
    @patch("pipeline.cli.s0_editorial_plan")
    @patch("pipeline.cli.argparse.ArgumentParser.parse_args")
    def test_cli_plan_mode(self, mock_args, mock_s0, mock_exit):
        mock_args.return_value = MagicMock(mode="plan", dry_run=False, verbose=False)
        mock_s0.run.return_value = {"articles": [{"type": "news", "priority": 1, "topic": "Test"}]}

        from pipeline.cli import cli
        cli()
        mock_s0.run.assert_called_once()

    @patch("pipeline.cli.sys.exit")
    @patch("pipeline.cli.argparse.ArgumentParser.parse_args")
    def test_cli_dry_run(self, mock_args, mock_exit):
        mock_args.return_value = MagicMock(mode="generate", dry_run=True, verbose=False)

        with patch("pipeline.modes.generate.run", return_value=[]) as mock_gen:
            from pipeline.cli import cli
            cli()
            mock_gen.assert_called_once_with(dry_run=True)

    @patch("pipeline.cli.sys.exit")
    @patch("pipeline.cli.argparse.ArgumentParser.parse_args")
    def test_cli_publish_nothing_exits_1(self, mock_args, mock_exit):
        mock_args.return_value = MagicMock(mode="publish", dry_run=False, verbose=False)

        with patch("pipeline.modes.publish.run", return_value=None):
            from pipeline.cli import cli
            cli()
            mock_exit.assert_called_with(1)

    @patch("pipeline.cli.sys.exit")
    @patch("pipeline.cli.argparse.ArgumentParser.parse_args")
    def test_cli_digest_nothing_exits_1(self, mock_args, mock_exit):
        mock_args.return_value = MagicMock(mode="digest", dry_run=False, verbose=False)

        with patch("pipeline.modes.digest.run", return_value=None):
            from pipeline.cli import cli
            cli()
            mock_exit.assert_called_with(1)

    @patch("pipeline.cli.sys.exit")
    @patch("pipeline.cli.argparse.ArgumentParser.parse_args")
    def test_cli_exception_exits_1(self, mock_args, mock_exit):
        mock_args.return_value = MagicMock(mode="generate", dry_run=False, verbose=False)

        with patch("pipeline.modes.generate.run", side_effect=Exception("Pipeline crashed")):
            from pipeline.cli import cli
            cli()
            mock_exit.assert_called_with(1)

    @patch("pipeline.cli.sys.exit")
    @patch("pipeline.cli.argparse.ArgumentParser.parse_args")
    def test_cli_keyboard_interrupt(self, mock_args, mock_exit):
        mock_args.return_value = MagicMock(mode="generate", dry_run=False, verbose=False)

        with patch("pipeline.modes.generate.run", side_effect=KeyboardInterrupt()):
            from pipeline.cli import cli
            cli()
            mock_exit.assert_called_with(130)
