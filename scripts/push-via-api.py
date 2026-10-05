#!/usr/bin/env python3
"""
push-via-api.py — git push 不稳（HTTP2 framing / CONNECT tunnel 502）时的兜底推送

用 GitHub Git Data API 做单次原子提交：
  - 新增/修改：blob → 挂到 base_tree → 新 tree → 新 commit → PATCH ref
  - 删除：contents API（需远程 blob sha），在 PATCH ref 之后逐个执行

注意：删除操作会产生额外 commit（contents API 无法塞进同一个 commit）。
      如果 ref 已被 Git Data API 推进到不含被删文件的状态，contents DELETE 会 404，
      此时视为已删除、跳过。

用法：python3 push-via-api.py "<commit message>" [file ...]
     不给文件列表时自动取「本地 HEAD 相对远程 main 的差异」（含未 commit 的工作区改动）
"""
import base64
import json
import os
import subprocess
import sys

REPO = os.environ.get("GITHUB_REPO", "BeringZ/diy-tools")
BRANCH = os.environ.get("GITHUB_BRANCH", "main")
API = f"repos/{REPO}"


def gh(args: list[str], stdin: str | None = None, allow_fail: bool = False) -> str | None:
    cmd = ["gh", "api", *args]
    proc = subprocess.run(
        cmd, input=stdin if stdin is not None else None, capture_output=True, text=True
    )
    if proc.returncode != 0:
        if allow_fail:
            return None
        sys.exit(f"[ERROR] gh api 失败: {' '.join(args[:4])}\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def remote_file_sha(path: str) -> str | None:
    out = gh([f"{API}/contents/{path}", "--jq", ".sha"], allow_fail=True)
    return out


def read_local(path: str) -> bytes | None:
    if os.path.exists(path) and os.path.isfile(path):
        with open(path, "rb") as f:
            return f.read()
    # 工作区没有则试 git（可能被删了）
    proc = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True)
    return proc.stdout if proc.returncode == 0 else None


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    message = sys.argv[1]

    base_sha = gh([f"{API}/git/refs/heads/{BRANCH}", "--jq", ".object.sha"])
    base_tree = gh([f"{API}/git/commits/{base_sha}", "--jq", ".tree.sha"])
    print(f"远程 base: {base_sha[:10]}")

    if len(sys.argv) > 2:
        files = sys.argv[2:]
    else:
        files = subprocess.run(
            ["git", "diff", "--name-only", base_sha, "HEAD"],
            capture_output=True, text=True,
        ).stdout.strip().splitlines()
    if not files:
        sys.exit("[ERROR] 无文件差异")
    print(f"变更文件: {files}")

    upserts, deletes = [], []
    for f in files:
        content = read_local(f)
        if content is None:
            deletes.append(f)
            print(f"  删除 {f}")
            continue
        b64 = base64.b64encode(content).decode()
        blob = gh([
            f"{API}/git/blobs", "--method", "POST",
            "-f", f"content={b64}", "-f", "encoding=base64", "--jq", ".sha",
        ])
        upserts.append({"path": f, "mode": "100755" if os.access(f, os.X_OK) else "100644",
                        "type": "blob", "sha": blob})
        print(f"  upsert {f}: {blob[:10]}")

    if upserts:
        new_tree = gh(
            [f"{API}/git/trees", "--method", "POST", "--input", "-", "--jq", ".sha"],
            stdin=json.dumps({"base_tree": base_tree, "tree": upserts}),
        )
        new_commit = gh(
            [f"{API}/git/commits", "--method", "POST", "--input", "-", "--jq", ".sha"],
            stdin=json.dumps({"message": message, "tree": new_tree, "parents": [base_sha]}),
        )
        gh([f"{API}/git/refs/heads/{BRANCH}", "--method", "PATCH",
            "-f", f"sha={new_commit}", "--jq", ".object.sha"])
        print(f"ref 已更新: {new_commit[:10]}")
    else:
        new_commit = base_sha
        print("无 upsert，仅处理删除")

    for f in deletes:
        sha = remote_file_sha(f)
        if not sha:
            print(f"  {f} 远程已不存在，跳过")
            continue
        out = gh([
            f"{API}/contents/{f}", "--method", "DELETE",
            "-f", f"message={message}", "-f", f"sha={sha}", "-f", f"branch={BRANCH}",
            "--jq", ".commit.sha",
        ], allow_fail=True)
        print(f"  已删除 {f}: {out[:10] if out else 'FAILED'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
