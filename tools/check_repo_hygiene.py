import subprocess

BAD_PATTERNS = (
    "__pycache__/",
    ".pyc",
    "scripts/cloud_cache/",
)


def tracked_files() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def main() -> int:
    files = tracked_files()
    violations: list[str] = []

    for file in files:
        normalized = file.replace("\\", "/")
        if any(p in normalized for p in BAD_PATTERNS):
            violations.append(file)

    if violations:
        print("Repo hygiene check failed. Remove tracked runtime/build artifacts:")
        for v in violations:
            print(f" - {v}")
        return 1

    print("Repo hygiene check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
