from operator import itemgetter

import datetime
import praw
import time

USER_AGENT = "script:nz.co.jacksteel.weeklyreport:v0.0.1 (by /u/iPlain)"

# Variables to Change
subs = [
    ['RequestABot', '']
]

# Global Submission Variables
submission_data = []  # Submission_Title, Submission_Author, Submission_Short_Link, Submission_Score, Submission_Short_Link, Submission_Created_Epoch, Submission_Created_GMT
top_submissions = ['Score|Author|Post Title', ':---|:---|:---']
gilded_submissions = ['Score|Author|Post Title|Gilded', ':---|:---|:---|:---']
submission_authors = []  # Total_Score, Author, Count
total_submission_count = 0
top_submission_authors = ['Author|Total Score|Submission Count|Submission Average', ':---|:---|:---|:---']
total_submission_authors = 0

# Global Comment Variables
comment_data = []  # Comment_Author, Comment_Score, Comment_Link, Submission_Title
top_comments = ['Score|Author|Comment', ':---|:---|:---']
gilded_comments = ['Score|Author|Comment|Gilded', ':---|:---|:---|:---']
comment_authors = []  # Total_Score, Author, Count
total_comment_count = 0
top_comment_authors = ['Author|Total Score|Comment Count|Comment Average', ':---|:---|:---|:---']
total_comment_authors = 0


def main():

    # Login
    r = praw.Reddit(
        username=USERNAME,
        password=PASSWORD,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT
    )

    # Loop
    for s in subs:
        subname = s[0]
        post_to_sub = s[1]

        run_report(subname, post_to_sub, r)

    return


def run_report(subname, post_to_sub, r):
    sub = r.subreddit(subname)

    print('Running Report for ' + subname)

    gather_data(sub)
    process_submission_data()
    process_comment_data()
    submit_report(r)

    reset_variables()

    return


def gather_data(sub):
    print('Gathering Data')

    global submission_data
    global gilded_submissions
    global comment_data
    global gilded_comments

    # Gather submissions from the week
    epoch_a_week_ago = time.time() - 604800

    submissions = sub.new(limit=None)
    # submissions = sub.search("", time_filter="year")

    c = 0

    # Go through each submission
    for submission in submissions:
        c += 1
        print(c)
        if submission.created_utc < epoch_a_week_ago:
            return
        # Disregard deleted or removed posts
        if submission.author:
            submission_data_row = []

            submission_data_row.append(submission.title) #Submission_Title
            submission_data_row.append("/u/" + submission.author.name) #Submission_Author
            submission_data_row.append(submission.url) #Submission_Short_Link
            submission_data_row.append(int(submission.score)) #Submission_Score
            submission_data_row.append(submission.url) #Submission_Short_Link
            submission_data_row.append(float(submission.created_utc)) #Submission_Created_Epoch
            submission_data_row.append(str(time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(float(submission.created_utc))))) #Submission_Created_GMT

            submission_data.append(submission_data_row)

            # Add gilded submissions to list
            if submission.gilded > 0:
                gilded_submissions.append(str(
                    submission.score) + '|/u/' + submission.author.name + '|[' + submission.title + '](' +')|' + str(
                    submission.gilded) + 'X')

            # Get the comments
            submission.comments.replace_more(limit=0)
            comments = submission.comments.list()
            # comments = None

            # Disregard submissions with no comments
            if comments:

                # Go through each comment
                for comment in comments:
                    # Disregard deleted comments
                    if comment.author and comment.banned_by == None:

                        comment_data_row = []

                        comment_data_row.append('/u/' + comment.author.name)  # Comment_Author
                        comment_data_row.append(int(comment.score))  # Comment_Score
                        comment_data_row.append(comment.permalink)  # Comment_Link
                        comment_data_row.append(submission.title)  # Submission_Title

                        comment_data.append(comment_data_row)

                        # Add gilded submissions to list
                        if comment.gilded > 0:
                            gilded_comments.append(str(
                                comment.score) + '|/u/' + comment.author.name + '|[' + submission.title + '](' + ')|' + str(
                                comment.gilded) + 'X')

    return


def process_submission_data():
    print('Processing Submissions')

    global submission_data
    global top_submissions
    global submission_authors
    global total_submission_count
    global top_submission_authors
    global total_submission_authors

    submission_data = reversed(sorted(submission_data, key=itemgetter(3)))

    for submission_data_row in submission_data:
        total_submission_count = total_submission_count + 1

        # Create Top 25 Submission Table
        if len(top_submissions) < 28:
            top_submissions.append(
                str(submission_data_row[3]) + '|' + str(submission_data_row[1]) + '|[' + submission_data_row[
                    0] + '](' + submission_data_row[2] + ')')

        # Compile Top Submission Author Scores
        if submission_authors:
            submission_author_exists = False
            for submission_author in submission_authors:
                if submission_data_row[1] == submission_author[1]:
                    submission_author[0] = submission_author[0] + submission_data_row[3]
                    submission_author[2] = submission_author[2] + 1
                    submission_author_exists = True
                    break
            if not submission_author_exists:
                submission_authors.append([submission_data_row[3], submission_data_row[1], 1])
        else:
            submission_authors.append([submission_data_row[3], submission_data_row[1], 1])

    # Compile Top Submission Author Table
    submission_authors = reversed(sorted(submission_authors, key=itemgetter(0)))

    for submission_author in submission_authors:

        try:

            total_submission_authors = total_submission_authors + 1
            if len(top_submission_authors) < 28:
                top_submission_authors.append(submission_author[1] + '|' + str(submission_author[0]) + '|' + str(
                    submission_author[2]) + '|' + str(int(float(submission_author[0]) / float(submission_author[2]))))
            else:
                break

        except Exception as e:

            print(e)

    return


def process_comment_data():
    print('Processing Comments')

    global comment_data  # Comment_Author, Comment_Score, Comment_Link, Submission_Title
    global top_comments
    global comment_authors  # Total_Score, Author, Count
    global total_comment_count
    global top_comment_authors
    global total_comment_authors

    comment_data = reversed(sorted(comment_data, key=itemgetter(1)))

    for comment_data_row in comment_data:

        try:

            total_comment_count = total_comment_count + 1

            # Create Top 25 Comments Table
            if len(top_comments) < 28:
                top_comments.append(
                    str(comment_data_row[1]) + '|' + str(comment_data_row[0]) + '|[' + comment_data_row[3] + '](' +
                    comment_data_row[2] + '?context=1000)')

            # Compile Top Comment Author Scores
            if comment_authors:
                comment_author_exists = False
                for comment_author in comment_authors:
                    if comment_data_row[0] == comment_author[1]:
                        comment_author[0] = comment_author[0] + comment_data_row[1]
                        comment_author[2] = comment_author[2] + 1
                        comment_author_exists = True
                        break
                if not comment_author_exists:
                    comment_authors.append([comment_data_row[1], comment_data_row[0], 1])
            else:
                comment_authors.append([comment_data_row[1], comment_data_row[0], 1])

        except (Exception) as e:

            print(e)

    # Compile Top Comment Author Table
    comment_authors = reversed(sorted(comment_authors, key=itemgetter(0)))

    for comment_author in comment_authors:

        try:

            total_comment_authors = total_comment_authors + 1
            if len(top_comment_authors) < 28:
                top_comment_authors.append(
                    str(comment_author[1]) + '|' + str(comment_author[0]) + '|' + str(comment_author[2]) + '|' + str(
                        int(float(comment_author[0]) / float(comment_author[2]))))

        except (Exception) as e:

            print(e)

    return


def submit_report(r):
    print('Compiling and Submitting Report')

    global subname
    global post_to_sub

    global submission_data
    global top_submissions
    global gilded_submissions
    global submission_authors
    global total_submission_count
    global top_submission_authors
    global total_submission_authors

    global comment_data
    global top_comments
    global gilded_comments
    global comment_authors
    global total_comment_count
    global top_comment_authors
    global total_comment_authors

    report_text = ['#Weekly Report for /r/' + subname]

    try:

        report_text.append(str(time.strftime('%A, %B %d, %Y', (
                datetime.datetime.now() + datetime.timedelta(days=-7)).timetuple())) + '  -  ' + str(
            time.strftime('%A, %B %d, %Y', time.gmtime())))
        report_text.append('---')

        report_text.append('---')
        report_text.append('#Submissions')
        report_text.append('---')

        report_text.append('---')
        report_text.append('Total Submissions: ' + str(total_submission_count))
        report_text.append('Total Submission Authors: ' + str(total_submission_authors))
        report_text.append('---')

        report_text.append('##Top 25 Submissions')
        report_text.append('\r\n'.join(top_submissions))
        report_text.append('---')

        report_text.append('##Top 25 Submitters')
        report_text.append('\r\n'.join(top_submission_authors))
        report_text.append('---')

        report_text.append('---')
        report_text.append(str(len(gilded_submissions) - 2) + ' Gilded Submissions')
        if len(gilded_submissions) > 2:
            report_text.append('\r\n'.join(gilded_submissions))
        report_text.append('---')

        report_text.append('---')
        report_text.append('#Comments')
        report_text.append('---')

        report_text.append('---')
        report_text.append('Total Comments: ' + str(total_comment_count))
        report_text.append('Total Comment Authors: ' + str(total_comment_authors))
        report_text.append('---')

        report_text.append('##Top 25 Comments')
        report_text.append('\r\n'.join(top_comments))
        report_text.append('---')

        report_text.append('##Top 25 Commenters')
        report_text.append('\r\n'.join(top_comment_authors))
        report_text.append('---')

        report_text.append('---')
        report_text.append(str(len(gilded_comments) - 2) + ' Gilded Comments')
        if len(gilded_comments) > 2:
            report_text.append('\r\n'.join(gilded_comments))
        report_text.append('---')

        report_text.append('---')
        report_text.append('^(created by /u/_korbendallas_)')
        report_text.append('---')

    except Exception as e:

        print(e)

    # Submit Report
    post_title = 'Weekly Report for /r/' + subname + ' - ' + str(time.strftime('%A, %B %d, %Y', time.gmtime()))

    try:

        print('\r\n\r\n'.join(report_text))
        # r.submit('WeeklyReport', post_title, text='\r\n\r\n'.join(report_text))

    except Exception as e:

        print('Error submitting post to WeeklyReport :', post_title)
        print(e)

    try:

        if not post_to_sub == '':
            r.submit(post_to_sub, post_title, text='\r\n\r\n'.join(report_text))

    except Exception as e:

        print('Error submitting post to', post_to_sub, ':', post_title)
        print(e)

    return


def reset_variables():
    global subname
    global post_to_sub

    global submission_data
    global top_submissions
    global gilded_submissions
    global submission_authors
    global total_submission_count
    global top_submission_authors
    global total_submission_authors

    global comment_data
    global top_comments
    global gilded_comments
    global comment_authors
    global total_comment_count
    global top_comment_authors
    global total_comment_authors

    subname = ''
    post_to_sub = ''

    submission_data = []
    top_submissions = ['Score|Author|Post Title', ':---|:---|:---']
    gilded_submissions = ['Score|Author|Post Title|Gilded', ':---|:---|:---|:---']
    submission_authors = []
    total_submission_count = 0
    top_submission_authors = ['Author|Total Score|Submission Count|Submission Average', ':---|:---|:---|:---']
    total_submission_authors = 0

    comment_data = []
    top_comments = ['Score|Author|Comment', ':---|:---|:---']
    gilded_comments = ['Score|Author|Comment|Gilded', ':---|:---|:---|:---']
    comment_authors = []
    total_comment_count = 0
    top_comment_authors = ['Author|Total Score|Comment Count|Comment Average', ':---|:---|:---|:---']
    total_comment_authors = 0

    return


main()
