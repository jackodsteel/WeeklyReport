#!/usr/bin/env python3
__author__ = "Jack Steel"

import collections
import datetime as dt
import time

import praw
from psaw import PushshiftAPI

USERNAME = ""
PASSWORD = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

USER_AGENT = "script:nz.co.jacksteel.weeklyreport:v0.0.1 (by /u/iPlain)"

SUBREDDIT = "RequestABot"


class AuthorData:
    total_score = 0
    count = 0

    def record_post(self, score):
        self.count += 1
        self.total_score += score

    def __gt__(self, other):
        return self.total_score > other.total_score


def main():
    print(create_report_body(SUBREDDIT))


def get_submissions(subreddit_name, reddit, pushshift, from_ago_epoch):
    submissions = []
    for submission in reddit.subreddit(subreddit_name).new(limit=None):
        if submission.created_utc < from_ago_epoch:
            break
        submissions.append(submission)
    if len(submissions) > 900:
        submissions += list(pushshift.search_submissions(subreddit=subreddit_name, after=from_ago_epoch,
                                                         before=submissions[-1].created_utc))
    return submissions


def get_comments(subreddit_name, reddit, pushshift, from_ago_epoch):
    comments = []
    for submission in reddit.subreddit(subreddit_name).comments(limit=None):
        if submission.created_utc < from_ago_epoch:
            break
        comments.append(submission)
    if len(comments) > 900:
        comments += list(pushshift.search_comments(subreddit=subreddit_name, after=from_ago_epoch,
                                                   before=comments[-1].created_utc))
    return comments


def create_reddit_table(column_names, data_extractor, data):
    column_names_str = " | ".join(column_names)
    column_formats_str = " | ".join([":--"] * len(column_names))
    mapped_data = map(data_extractor, data)
    mapped_data = map(lambda d: [str(x) for x in d], mapped_data)
    data_columns = map(lambda d: " | ".join(d), mapped_data)
    return column_names_str + "\n" + column_formats_str + "\n" + "\n".join(data_columns)


class ReportData:
    total_count = None
    total_authors_count = None
    top_entries_table = None
    top_authors_table = None
    gilded_entries_count = None
    gilded_entries_table = None


def process_data(data, data_column_title, type_name):
    """
    data should be a list of PRAW objects, either comments or submissions. They must also have a `data` and `link`
    attribute which you must add.
    """
    report_data = ReportData()
    report_data.total_count = len(data)

    authors = collections.defaultdict(AuthorData)
    for entry in data:
        authors[entry.author.name].record_post(entry.score)
    report_data.total_authors_count = len(authors)

    top_entries = list(sorted(data, key=lambda s: s.score, reverse=True))[:25]
    report_data.top_entries_table = create_reddit_table(
        ["Score", "Author", data_column_title],
        lambda e: [e.score, "/u/" + e.author.name, f"[{e.data}]({e.link})"],
        top_entries
    )

    top_authors = list(sorted(authors.items(), key=lambda kv: kv[1], reverse=True))[:25]
    report_data.top_authors_table = create_reddit_table(
        ["Author", "Total Score", type_name + " Count", type_name + " Average"],
        lambda n_d: ["/u/" + n_d[0], n_d[1].total_score, n_d[1].count, n_d[1].total_score // n_d[1].count],
        top_authors
    )

    gilded_entries = list(filter(lambda s: s.gilded > 0, data))
    report_data.gilded_entries_count = len(gilded_entries)
    report_data.gilded_entries_table = create_reddit_table(
        ["Score", "Author", data_column_title, "Gilded"],
        lambda e: [e.score, "/u/" + e.author.name, f"[{e.data}]({e.link})", f"{e.gilded}X"],
        gilded_entries
    )

    return report_data


def create_report_body(subreddit_name):
    reddit = praw.Reddit(
        username=USERNAME,
        password=PASSWORD,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT
    )
    pushshift = PushshiftAPI(r=reddit)

    time_now = dt.datetime.now()
    time_one_week_ago = time_now - dt.timedelta(days=7)
    time_one_week_ago_epoch = int(time_one_week_ago.timestamp())

    submissions = get_submissions(subreddit_name, reddit, pushshift, time_one_week_ago_epoch)
    for submission in submissions:
        submission.data = submission.title
        submission.link = submission.shortlink
    submission_report = process_data(submissions, "Post Title", "Submission")

    comments = get_comments(subreddit_name, reddit, pushshift, time_one_week_ago_epoch)
    for comment in comments:
        ind = next((i for i, ch in enumerate(comment.body) if ch in {'\n', '`'}), len(comment.body))
        ind = min(ind, 150)
        comment.data = comment.body[:ind]
        if ind < len(comment.body) - 2:
            comment.data += " ...\\[trimmed\\]"
        comment.link = comment.permalink
    comment_report = process_data(comments, "Comment Link", "Comment")


    return f"""
#Weekly Report for /r/{subreddit_name}
{time.strftime('%A, %B %d, %Y', time_one_week_ago.timetuple())}  -  {time.strftime('%A, %B %d, %Y', time_now.timetuple())}

---
---

#Submissions

---
---

Total Submissions: {submission_report.total_count}

Total Submission Authors: {submission_report.total_authors_count}

---

##Top 25 Submissions
{submission_report.top_entries_table}

---

##Top 25 Submitters
{submission_report.top_authors_table}

---
---

{submission_report.gilded_entries_count} Gilded Submissions
{submission_report.gilded_entries_table if submission_report.gilded_entries_count > 0 else ""}


#Comments

---
---

Total Comments: {comment_report.total_count}

Total Comment Authors: {comment_report.total_authors_count}

---

##Top 25 Comments
{comment_report.top_entries_table}

---

##Top 25 Commenters
{comment_report.top_authors_table}

---
---

{comment_report.gilded_entries_count} Gilded Comments
{comment_report.gilded_entries_table if comment_report.gilded_entries_count > 0 else ""}

---
---

^(created by /u/_korbendallas_ and updated by /u/iPlain)

---
"""


if __name__ == "__main__":
    main()
