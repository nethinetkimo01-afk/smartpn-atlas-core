#!/usr/bin/env python3
"""
Nightly automation runner for smartpn-atlas-core.

Features:
  - Loads all task modules from nightly/tasks/*.py
  - Runs each task in order, skips failures (never aborts)
  - Records per-task completion state in nightly/logs/STATE_YYYYMMDD.json
  - Supports checkpoint resume: already-completed tasks are skipped
  - Writes full log to nightly/logs/YYYYMMDD_HHMMSS.txt
  - Auto git commit + push origin main on completion

Usage:
    python nightly/run_nightly.py [--task <name>] [--force] [--no-push]

Options:
    --task <name>   Run only this specific task module (no state tracking)
    --force         Re-run all tasks even if already completed today
    --no-push       Skip the final git commit + push
"""
import sys, os, json, importlib, importlib.util, glob, subprocess, traceback
from datetime import datetime

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS  = os.path.join(ROOT, 'nightly', 'tasks')
LOGS   = os.path.join(ROOT, 'nightly', 'logs')

os.makedirs(LOGS, exist_ok=True)

NOW = datetime.now()
DATE_STR = NOW.strftime('%Y%m%d')
TS_STR   = NOW.strftime('%Y%m%d_%H%M%S')
LOG_FILE  = os.path.join(LOGS, f'{TS_STR}.txt')
STATE_FILE= os.path.join(LOGS, f'STATE_{DATE_STR}.json')


class Logger:
    def __init__(self, path):
        self.path = path
        self.fh = open(path, 'w', encoding='utf-8')

    def log(self, msg=''):
        ts = datetime.now().strftime('%H:%M:%S')
        line = f'[{ts}] {msg}'
        print(line)
        self.fh.write(line + '\n')
        self.fh.flush()

    def close(self):
        self.fh.close()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def git_commit_push(logger, message=None):
    if not message:
        message = f'nightly: auto-update {DATE_STR}'
    try:
        subprocess.run(['git', '-C', ROOT, 'add', '-A'], check=True, capture_output=True)
        result = subprocess.run(
            ['git', '-C', ROOT, 'status', '--porcelain'],
            capture_output=True, text=True
        )
        if not result.stdout.strip():
            logger.log('git: nothing to commit')
            return True

        subprocess.run(
            ['git', '-C', ROOT, 'commit', '-m', message],
            check=True, capture_output=True
        )
        subprocess.run(
            ['git', '-C', ROOT, 'push', 'origin', 'main'],
            check=True, capture_output=True
        )
        logger.log(f'git: committed + pushed — {message}')
        return True
    except subprocess.CalledProcessError as e:
        logger.log(f'git error: {e}')
        return False


def run_task_module(name, module, logger, state, force=False):
    """Run a single task module. Returns True if succeeded."""
    if not force and state.get(name) == 'done':
        logger.log(f'SKIP [{name}] (already done today)')
        return True

    logger.log(f'START [{name}]')
    state[name] = 'running'
    save_state(state)

    try:
        result = module.run(logger)
        if result is False:
            logger.log(f'FAIL  [{name}] returned False')
            state[name] = 'failed'
            save_state(state)
            return False
        else:
            logger.log(f'DONE  [{name}]')
            state[name] = 'done'
            save_state(state)
            return True
    except Exception:
        logger.log(f'ERROR [{name}]:\n{traceback.format_exc()}')
        state[name] = 'error'
        save_state(state)
        return False


def main():
    force   = '--force'   in sys.argv
    no_push = '--no-push' in sys.argv
    only_task = None
    if '--task' in sys.argv:
        idx = sys.argv.index('--task')
        if idx + 1 < len(sys.argv):
            only_task = sys.argv[idx + 1]

    logger = Logger(LOG_FILE)
    logger.log(f'=== Nightly Run {TS_STR} force={force} no_push={no_push} ===')

    # Load task modules
    task_files = sorted(glob.glob(os.path.join(TASKS, '*.py')))
    task_files = [f for f in task_files if not os.path.basename(f).startswith('_')]

    if only_task:
        task_files = [f for f in task_files if os.path.splitext(os.path.basename(f))[0] == only_task]
        if not task_files:
            logger.log(f'ERROR: task "{only_task}" not found in {TASKS}')
            logger.close()
            sys.exit(1)

    state = load_state()
    results = {}

    sys.path.insert(0, TASKS)
    sys.path.insert(0, ROOT)

    for tf in task_files:
        name = os.path.splitext(os.path.basename(tf))[0]
        try:
            spec = importlib.util.spec_from_file_location(name, tf)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception:
            logger.log(f'LOAD ERROR [{name}]:\n{traceback.format_exc()}')
            results[name] = False
            continue

        ok = run_task_module(name, mod, logger, state, force=force)
        results[name] = ok

    # Summary
    logger.log('')
    logger.log('=== Summary ===')
    ok_count = sum(1 for v in results.values() if v)
    fail_count = len(results) - ok_count
    for name, ok in results.items():
        logger.log(f'  {"OK  " if ok else "FAIL"} {name}')
    logger.log(f'Total: {ok_count} OK, {fail_count} failed')

    # Git commit + push
    if not no_push and not only_task:
        logger.log('')
        git_commit_push(logger, f'nightly {DATE_STR}: {ok_count}/{len(results)} tasks OK')

    logger.log(f'=== Done. Log: {LOG_FILE} ===')
    logger.close()
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == '__main__':
    main()
