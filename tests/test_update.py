"""Exercise the real updater with isolated Docker/HTTP fakes and a fast clock.

Run with: python3 -m unittest discover -s tests -v
No Docker daemon, network access, or third-party Python packages are required.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FAKE_COMMAND = r'''
import json
import os
from pathlib import Path
import signal
import sys

root = Path(os.environ["UPDATE_TEST_DIR"])
config = json.loads((root / "config.json").read_text())
tool = Path(sys.argv[0]).name
args = sys.argv[1:]
with (root / "calls.jsonl").open("a") as stream:
    stream.write(json.dumps([tool, *args]) + "\n")

def counter(name):
    path = root / name
    count = int(path.read_text()) if path.exists() else 0
    path.write_text(str(count + 1))
    return count

if tool == "curl":
    if any("raw.githubusercontent.com" in arg for arg in args):
        output = Path(args[args.index("-o") + 1])
        output.write_text((root / "remote.sh").read_text())
        sys.exit(config.get("download_exit", 0))
    if any("/health" in arg for arg in args):
        sys.exit(1 if config.get("http_failure") else 0)
    print("200")
elif tool == "mv":
    if config.get("replace_exit") and args[-1].endswith("/update.sh"):
        sys.exit(config["replace_exit"])
    os.replace(args[-2], args[-1])
elif args[:1] == ["create"]:
    # Simulate an older image without host-side sandbox configuration.
    sys.exit(1)
elif args[:1] == ["inspect"]:
    if config.get("interrupt"):
        os.kill(int(os.environ["UPDATE_TEST_PID"]), signal.SIGTERM)
        sys.exit(1)
    states = config.get("states", ["running healthy"])
    print(states[min(counter("inspections"), len(states) - 1)])
elif args[:1] == ["compose"]:
    if args[-2:] == ["config", "--services"]:
        print("db\nmyriade")
        if config.get("autoheal", True):
            print("autoheal")
    elif args[1:3] == ["exec", "myriade"]:
        print("v1.0.0")
    elif "ps" in args and args[-1] == "myriade":
        if not config.get("missing_container"):
            print("app-container")
    elif args[1:3] == ["pull", "myriade"]:
        sys.exit(config.get("pull_exit", 0))
    elif args[1:3] == ["stop", "autoheal"]:
        sys.exit(config.get("stop_exit", 0))
    elif args[1:2] == ["up"]:
        key = "app_exit" if args[-1] == "myriade" else "autoheal_exit"
        sys.exit(config.get(key, 0))
'''


class UpdateTest(unittest.TestCase):
    def run_update(self, config=None, timeout="1800", *, refresh=False, remote=None, args=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "setup").mkdir()
            (root / "bin").mkdir()
            shutil.copy(ROOT / "setup/update.sh", root / "setup/update.sh")
            original = (ROOT / "setup/update.sh").read_text()
            (root / "remote.sh").write_text(original if remote is None else remote)
            (root / "docker-compose.yml").write_text("services: {}\n")
            (root / ".env").write_text("MYRIADE_HTTP_PORT=8181\n")
            (root / "config.json").write_text(json.dumps(config or {}))
            for command in ("docker", "curl", "mv"):
                executable = root / "bin" / command
                executable.write_text(f"#!{sys.executable}\n" + FAKE_COMMAND)
                executable.chmod(0o755)
            env = os.environ.copy()
            env.pop("SANDBOX_TOKEN", None)
            env.pop("MYRIADE_HTTP_PORT", None)
            env.update(
                PATH=f"{root / 'bin'}:{env['PATH']}",
                UPDATE_TEST_DIR=str(root),
                MYRIADE_UPDATE_TIMEOUT=timeout,
                MYRIADE_SKIP_SELF_UPDATE="0" if refresh else "1",
            )
            result = subprocess.run(
                ["bash", "-c", '''
                    source "$1/setup/update.sh"
                    NGINX_SITE="$1/no-nginx"
                    export UPDATE_TEST_PID=$$
                    sleep() { SECONDS=$((SECONDS + 60)); }
                    shift
                    main "$@"
                ''', "test-update", str(root), *(args if args is not None else ["latest"])],
                env=env, text=True, capture_output=True, timeout=15,
            )
            log = root / "calls.jsonl"
            calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
            self.artifacts = {
                str(path.relative_to(root)): path.read_text()
                for path in root.rglob("*") if path.is_file() and path.parent != root / "bin"
            }
            self.installed_mode = (root / "setup/update.sh").stat().st_mode & 0o777
            return result, calls

    def assert_not_resumed(self, calls):
        self.assertFalse(any(call[:3] == ["docker", "compose", "up"]
                             and call[-1] == "autoheal" for call in calls))

    def test_slow_migration_finishes_before_autoheal_resumes(self):
        result, calls = self.run_update({"states": ["running unhealthy"] * 10 + ["running healthy"]})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        stop = calls.index(["docker", "compose", "stop", "autoheal"])
        start = calls.index(["docker", "compose", "up", "-d", "--no-build", "myriade"])
        resume = calls.index(["docker", "compose", "up", "-d", "--no-build", "--no-deps", "autoheal"])
        self.assertLess(stop, start)
        inspections = [i for i, call in enumerate(calls) if call[:2] == ["docker", "inspect"]]
        self.assertEqual(len(inspections), 11)
        self.assertLess(inspections[-1], resume)
        probes = [(i, call) for i, call in enumerate(calls) if call[0] == "curl"]
        self.assertEqual(len(probes), 1)
        self.assertLess(inspections[-1], probes[0][0])
        self.assertLess(probes[0][0], resume)
        self.assertIn("http://localhost:8181/health", probes[0][1])
        self.assertIn("--max-time", probes[0][1])
        self.assertIn("Update complete!", result.stdout)

    def test_timeout_keeps_migration_running_and_autoheal_stopped(self):
        result, calls = self.run_update({"states": ["running unhealthy"]}, timeout="120")
        self.assertNotEqual(result.returncode, 0)
        self.assert_not_resumed(calls)
        self.assertIn("Autoheal remains stopped", result.stdout)
        self.assertIn("left running", result.stdout)
        self.assertNotIn("Update complete!", result.stdout)
        self.assertFalse(any(call[:3] == ["docker", "compose", "stop"]
                             and call[-1] == "myriade" for call in calls))

    def test_http_failure_does_not_resume_autoheal(self):
        result, calls = self.run_update({"http_failure": True}, timeout="120")
        self.assertNotEqual(result.returncode, 0)
        self.assert_not_resumed(calls)

    def test_terminal_container_states_fail_immediately(self):
        for state in ("exited unhealthy", "dead none", "restarting unhealthy"):
            with self.subTest(state=state):
                result, calls = self.run_update({"states": [state]})
                self.assertNotEqual(result.returncode, 0)
                self.assert_not_resumed(calls)
                self.assertEqual(sum(call[:2] == ["docker", "inspect"] for call in calls), 1)

    def test_no_autoheal_service(self):
        result, calls = self.run_update({"autoheal": False})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any("autoheal" in call for call in calls))

    def test_no_docker_healthcheck_uses_http_readiness(self):
        result, calls = self.run_update({"states": ["running none"]})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(any(call[0] == "curl" for call in calls))

    def test_pull_failure_does_not_stop_autoheal(self):
        result, calls = self.run_update({"pull_exit": 1})
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(["docker", "compose", "stop", "autoheal"], calls)

    def test_stop_failure_aborts_before_recreating_application(self):
        result, calls = self.run_update({"stop_exit": 1})
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any(call[:3] == ["docker", "compose", "up"] for call in calls))

    def test_start_failure_or_missing_container_leaves_autoheal_stopped(self):
        for config in ({"app_exit": 1}, {"missing_container": True}):
            with self.subTest(config=config):
                result, calls = self.run_update(config)
                self.assertNotEqual(result.returncode, 0)
                self.assert_not_resumed(calls)
                self.assertIn("Autoheal remains stopped", result.stdout)

    def test_autoheal_resume_failure_is_reported(self):
        result, _ = self.run_update({"autoheal_exit": 1})
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Update complete!", result.stdout)
        self.assertIn("Autoheal remains stopped", result.stdout)

    def test_interruption_leaves_autoheal_stopped(self):
        result, calls = self.run_update({"interrupt": True})
        self.assertEqual(result.returncode, 143, result.stdout + result.stderr)
        self.assert_not_resumed(calls)
        self.assertIn("Autoheal remains stopped", result.stdout)

    def test_invalid_timeouts_fail_before_service_changes(self):
        for timeout in ("0", "-1", "garbage", "01", "86401", "999999999999999999999"):
            with self.subTest(timeout=timeout):
                result, calls = self.run_update(timeout=timeout)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, [])
                self.assertIn("MYRIADE_UPDATE_TIMEOUT must be", result.stdout)

    def assert_refresh_cleaned_up(self):
        self.assertFalse(any(path.startswith("setup/.update.sh.") for path in self.artifacts))

    def test_unchanged_updater_continues_without_replacing_itself(self):
        result, calls = self.run_update(refresh=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("setup/update.sh.previous", self.artifacts)
        self.assertEqual(calls[0][0], "curl")
        self.assertIn("https://raw.githubusercontent.com/myriade-ai/myriade/master/setup/update.sh", calls[0])
        self.assert_refresh_cleaned_up()

    def test_refreshed_updater_runs_once_preserving_arguments_and_environment(self):
        original = (ROOT / "setup/update.sh").read_text()
        remote = original.replace("main() {", '''main() {
    printf '<%s>\\n' "$@" > "$UPDATE_TEST_DIR/arguments"
    printf '%s' "$MYRIADE_UPDATE_TIMEOUT" > "$UPDATE_TEST_DIR/timeout"
    echo "RUNNING_REFRESHED_UPDATER"
''')
        result, calls = self.run_update(refresh=True, remote=remote, args=["1.165.0"], timeout="3600")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.count("RUNNING_REFRESHED_UPDATER"), 1)
        downloads = [call for call in calls if any("raw.githubusercontent.com" in arg for arg in call)]
        self.assertEqual(len(downloads), 1)
        self.assertEqual(self.artifacts["arguments"], "<1.165.0>\n")
        self.assertEqual(self.artifacts["timeout"], "3600")
        self.assertEqual(self.artifacts["setup/update.sh"], remote)
        self.assertEqual(self.artifacts["setup/update.sh.previous"], original)
        self.assertEqual(self.installed_mode, 0o755)
        self.assertIn("Update complete!", result.stdout)
        self.assert_refresh_cleaned_up()

    def test_download_failure_preserves_script_and_does_not_touch_docker(self):
        original = (ROOT / "setup/update.sh").read_text()
        result, calls = self.run_update({"download_exit": 28}, refresh=True, remote="partial download")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.artifacts["setup/update.sh"], original)
        self.assertFalse(any(call[0] == "docker" for call in calls))
        self.assertIn("MYRIADE_SKIP_SELF_UPDATE=1", result.stdout)
        self.assert_refresh_cleaned_up()

    def test_invalid_downloads_are_never_installed_or_executed(self):
        original = (ROOT / "setup/update.sh").read_text()
        for remote in ("", "<html>Error</html>", "#!/bin/bash\nexit 0\n",
                       "#!/bin/bash\n# Myriade Self-Hosted Update Script\nexit 0\n",
                       "#!/bin/bash\n# Myriade Self-Hosted Update Script\n# Self-update protocol: 1\nif then\n"):
            with self.subTest(remote=remote):
                result, calls = self.run_update(refresh=True, remote=remote)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.artifacts["setup/update.sh"], original)
                self.assertNotIn("setup/update.sh.previous", self.artifacts)
                self.assertFalse(any(call[0] == "docker" for call in calls))
                self.assert_refresh_cleaned_up()

    def test_replace_failure_keeps_original_and_backup_without_touching_services(self):
        original = (ROOT / "setup/update.sh").read_text()
        result, calls = self.run_update({"replace_exit": 1}, refresh=True, remote=original + "\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.artifacts["setup/update.sh"], original)
        self.assertEqual(self.artifacts["setup/update.sh.previous"], original)
        self.assertFalse(any(call[0] == "docker" for call in calls))
        self.assert_refresh_cleaned_up()

    def test_new_updater_failure_is_propagated_without_running_old_deployment(self):
        remote = "#!/bin/bash\n# Myriade Self-Hosted Update Script\n# Self-update protocol: 1\nexit 42\n"
        result, calls = self.run_update(refresh=True, remote=remote)
        self.assertEqual(result.returncode, 42)
        self.assertFalse(any(call[0] == "docker" for call in calls))
        self.assert_refresh_cleaned_up()

    def test_versions_does_not_self_update(self):
        result, calls = self.run_update(refresh=True, args=["versions"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any("raw.githubusercontent.com" in arg for call in calls for arg in call))
        self.assertNotIn("setup/update.sh.previous", self.artifacts)

    def test_explicit_opt_out_uses_local_script(self):
        result, calls = self.run_update({"download_exit": 28}, refresh=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any("raw.githubusercontent.com" in arg for call in calls for arg in call))


if __name__ == "__main__":
    unittest.main()
