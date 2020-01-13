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
    total_submission_count = len(submissions)

    submission_authors = collections.defaultdict(AuthorData)
    for submission in submissions:
        submission_authors[submission.author.name].record_post(submission.score)
    total_submission_authors = len(submission_authors)

    top_submissions = list(sorted(submissions, key=lambda s: s.score, reverse=True))[:25]
    top_submissions_table = create_reddit_table(
        ["Score", "Author", "Post Title"],
        lambda s: [s.score, "/u/" + s.author.name, f"[{s.title}]({s.shortlink})"],
        top_submissions
    )

    top_submitters = list(sorted(submission_authors.items(), key=lambda kv: kv[1], reverse=True))[:25]
    top_submitters_table = create_reddit_table(
        ["Author", "Total Score", "Submission Count", "Submission Average"],
        lambda name_d: ["/u/" + name_d[0], name_d[1].total_score, name_d[1].count, name_d[1].total_score // name_d[1].count],
        top_submitters
    )

    gilded_submissions = list(filter(lambda s: s.gilded > 0, submissions))
    gilded_submissions_table = create_reddit_table(
        ["Score", "Author", "Post Title", "Gilded"],
        lambda s: [s.score, "/u/" + s.author.name, f"[{s.title}]({s.shortlink})", f"{s.gilded}X"],
        gilded_submissions
    )

    comments = get_comments(subreddit_name, reddit, pushshift, time_one_week_ago_epoch)
    total_comment_count = len(comments)

    comment_authors = collections.defaultdict(AuthorData)
    for comment in comments:
        comment_authors[comment.author.name].record_post(comment.score)
    total_comment_authors = len(comment_authors)

    top_comments = list(sorted(comments, key=lambda s: s.score, reverse=True))[:25]
    top_comments_table = create_reddit_table(
        ["Score", "Author", "Comment Link"],
        lambda s: [s.score, "/u/" + s.author.name, f"[{s.submission.title}]({s.permalink})"],
        top_comments
    )

    top_commenters = list(sorted(comment_authors.items(), key=lambda kv: kv[1], reverse=True))[:25]
    top_commenters_table = create_reddit_table(
        ["Author", "Total Score", "Comment Count", "Comment Average"],
        lambda name_d: ["/u/" + name_d[0], name_d[1].total_score, name_d[1].count, name_d[1].total_score // name_d[1].count],
        top_commenters
    )

    gilded_comments = list(filter(lambda s: s.gilded > 0, comments))
    gilded_comments_table = create_reddit_table(
        ["Score", "Author", "Comment Link", "Gilded"],
        lambda s: [s.score, "/u/" + s.author.name, f"[{s.submission.title}]({s.permalink})", f"{s.gilded}X"],
        gilded_comments
    )

    return f"""
#Weekly Report for /r/{subreddit_name}
{time.strftime('%A, %B %d, %Y', time_one_week_ago.timetuple())}  -  {time.strftime('%A, %B %d, %Y', time_now.timetuple())}

---
---

#Submissions

---
---

Total Submissions: {total_submission_count}

Total Submission Authors: {total_submission_authors}

---

##Top 25 Submissions
{top_submissions_table}

---

##Top 25 Submitters
{top_submitters_table}

---
---

{len(gilded_submissions)} Gilded Submissions
{gilded_submissions_table if len(gilded_submissions) > 0 else ""}


#Comments

---
---

Total Comments: {total_comment_count}

Total Comment Authors: {total_comment_authors}

---

##Top 25 Comments
{top_comments_table}

---

##Top 25 Commenters
{top_commenters_table}

---
---

{len(gilded_comments)} Gilded Comments
{gilded_comments_table if len(gilded_comments) > 0 else ""}

---
---

^(created by /u/_korbendallas_ and updated by /u/iPlain)

---
"""


if __name__ == "__main__":
    main()
