#!/usr/bin/env python3
"""
GitHub Issues dataset downloader for NLP risk testing.
Downloads issues from public GitHub repositories for testing the RiskNLPEngine.
"""

import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import urllib.parse


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | github_issues_loader | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("logs/data_download.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean text by removing HTML, markdown, and code blocks."""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove markdown links
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove code blocks
    text = re.sub(r"```[^`]*```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_bot_comment(user_login: str) -> bool:
    """Check if a comment is from a bot."""
    bot_keywords = ["dependabot", "renovate", "codecov", "bot"]
    return any(keyword in user_login.lower() for keyword in bot_keywords)


def download_github_issues(owner: str, repo: str, num_issues: int = 300) -> List[Dict]:
    """Download GitHub issues from a repository."""
    logger = setup_logging()
    issues = []

    # GitHub API base URL
    base_url = f"https://api.github.com/repos/{owner}/{repo}/issues"

    # Add query parameters for pagination
    params = {
        "state": "all",  # Get both open and closed issues
        "per_page": 100,  # Max per page
        "page": 1,
    }

    headers = {
        "User-Agent": "RiskAI-Framework-Data-Loader/1.0",
        "Accept": "application/vnd.github.v3+json",
    }

    total_chars = 0
    downloaded_count = 0

    while len(issues) < num_issues:
        # Build URL with parameters
        url = f"{base_url}?per_page=100&page={params['page']}"
        req = Request(url, headers=headers)

        try:
            with urlopen(req) as response:
                import json as json_lib

                page_issues = json_lib.loads(response.read())

            if not page_issues:
                break

            for issue in page_issues:
                if "pull_request" in issue:
                    continue

                issue_id = issue.get("number")
                issue_title = issue.get("title", "")
                body = clean_text(issue.get("body", ""))
                html_url = issue.get("html_url", "")

                comments_url = issue.get("comments_url", "")
                comments: List[str] = []
                comment_count = 0

                if comments_url and issue.get("comments", 0) > 0:
                    comments_req = Request(comments_url, headers=headers)
                    try:
                        with urlopen(comments_req) as comments_response:
                            issue_comments = json_lib.loads(comments_response.read())
                        for comment in issue_comments[:5]:
                            user_login = comment.get("user", {}).get("login", "")
                            if is_bot_comment(user_login):
                                continue
                            comment_body = clean_text(comment.get("body", ""))
                            if len(comment_body) > 20:
                                comments.append(comment_body)
                                comment_count += 1
                    except Exception as e:
                        logger.warning(
                            f"Failed to fetch comments for issue {issue_id}: {e}"
                        )

                combined_text = f"{issue_title}. {body}".strip()
                for comment in comments:
                    combined_text += f" {comment}"

                issue_record = {
                    "text": combined_text,
                    "issue_id": issue_id,
                    "issue_title": issue_title,
                    "comment_count": comment_count,
                    "url": html_url,
                }

                issues.append(issue_record)
                total_chars += len(combined_text)
                downloaded_count += 1

                if downloaded_count >= num_issues:
                    break

            params["page"] += 1
            time.sleep(0.1)

        except HTTPError as e:
            if e.code == 403:
                logger.error("Rate limited. Please try again later.")
                break
            logger.error(f"HTTP Error: {e}")
            break
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            break

    return issues


def save_issues(issues: List[Dict], owner: str, repo: str, num_issues: int):
    """Save issues to JSON file."""
    # Calculate total characters
    total_chars = sum(len(issue.get("text", "")) for issue in issues)

    output = {
        "metadata": {
            "download_date": datetime.now().isoformat(),
            "repo": f"{owner}/{repo}",
            "num_issues": num_issues,
            "total_chars": total_chars,
        },
        "issues": issues,
    }

    # Save to file
    with open(
        f"data/github_issues_{owner}_{repo}.json".lower().replace("/", "_"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download GitHub issues for NLP risk testing"
    )
    parser.add_argument("--owner", required=True, help="GitHub organization/user")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument(
        "--count", type=int, default=300, help="Number of issues to download"
    )

    args = parser.parse_args()

    issues = download_github_issues(args.owner, args.repo, args.count)
    save_issues(issues, args.owner, args.repo, args.count)

    print(f"Downloaded {len(issues)} issues from {args.owner}/{args.repo}")


if __name__ == "__main__":
    main()
