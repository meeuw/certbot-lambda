"""
AWS Lambda function to request Letsencrypt certificates using Certbot
Uses S3 as persistent storage of the certificates, keyfiles and logfiles.
"""
import os
import json
import stat
import subprocess
import shutil
import shlex


def pyrun(cmd, args):
    """
    SAM build doesn't add the scripts in bin/ for awscli and certbot.
    This is a simple substitude for that
    """
    subprocess.check_call(
        [
            "python",
            "-c",
            f"import os, sys ; sys.path.append(os.environ['LAMBDA_TASK_ROOT'] ) ; {cmd}",
        ]
        + args
    )


def awscli(args):
    pyrun("import awscli.clidriver ; awscli.clidriver.main()", args)


def certbot(args):
    pyrun("import certbot.main ; certbot.main.main()", args)


def lambda_handler(event, context):
    dirs = {"root": "/tmp"}
    dirs["workdir"] = dirs["root"] + "/workdir"
    dirs["logs"] = dirs["root"] + "/logs"

    for d in dirs.values():
        if not os.path.exists(d):
            os.makedirs(d, 0o700)

    os.chdir(dirs["root"])

    if os.path.exists("live"):
        shutil.rmtree("live")

    awscli(
        [
            "s3",
            "sync",
            "--delete",
            "--no-progress",
            "--exclude",
            "live/*/*",
            f"s3://{os.environ['CERTBOTBUCKET']}/",
            "./",
        ]
    )

    if os.path.exists("symlinks.json"):
        deserialize_symlinks()

    certbot(
        [
            "certonly",
            "--dns-route53",
            "--quiet",
            "--agree-tos",
            "--keep-until-expiring",
            "--work-dir",
            dirs["workdir"],
            "--config-dir",
            dirs["root"],
            "--logs-dir",
            dirs["logs"],
            "--preferred-challenges=dns",
        ]
        + shlex.split(os.environ["CERTBOTARGS"])
    )

    serialize_symlinks()

    awscli(
        [
            "s3",
            "sync",
            "--delete",
            "--no-progress",
            "./",
            f"s3://{os.environ['CERTBOTBUCKET']}/",
        ]
    )

    return {"message": "done"}


def deserialize_symlinks():
    """
    Create symlinks as defined in symlinks.json
    """
    with open("symlinks.json", "r") as f:
        symlinks = json.load(f)
    for s in symlinks:
        os.makedirs(os.path.dirname(s["dst"]), exist_ok=True)
        os.symlink(s["src"], s["dst"])


def serialize_symlinks():
    """
    Create symlinks.json from files/directories in live/ directory
    """
    symlinks = []
    for root, _, files in os.walk("live"):
        for file in files:
            dst = os.path.join(root, file)
            s = os.stat(dst, follow_symlinks=False)
            if stat.S_ISLNK(s.st_mode):
                symlinks.append(
                    {
                        "src": os.readlink(dst),
                        "dst": dst,
                    }
                )

    with open("symlinks.json", "w") as f:
        json.dump(symlinks, f, indent=4)


if __name__ == "__main__":
    lambda_handler(None, None)
