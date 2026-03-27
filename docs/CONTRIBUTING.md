# Contributing

First of all, thank you for considering contributing!

This project is in **early and active development**, and we are actively
looking for contributors. Even if you're just getting started with QML,
Qt Quick, or Python, you're very welcome to contribute — small contributions
are just as valuable!

If you're a student or new to open source, this is a great place to start.

⚠️ **Important:** The repository on GitHub is a read-only mirror. We do not
accept GitHub Pull Requests. Instead, we use **Gerrit** for code review.

## Qt Account

Before contributing, you need to create a [Qt account](https://login.qt.io/register).
This account is used to authenticate you across Bug tracker, Gerrit and Wiki.

## Ways to Contribute

There are many ways you can help:

- Fix issues
- Report bugs
- Suggest new features
- Improve documentation

## Getting the Source Code

Clone the repository from the official source with git hooks:

```shell
git clone "https://codereview.qt-project.org/qt/qtbridge-python" && (cd "qtbridge-python" && mkdir -p `git rev-parse \
 --git-dir`/hooks/ && curl -Lo `git rev-parse \
 --git-dir`/hooks/commit-msg https://codereview.qt-project.org/tools/hooks/commit-msg && chmod +x \
 `git rev-parse --git-dir`/hooks/commit-msg)

cd qtbridge-python
git checkout dev
```

## Configure Gerrit

Log into [Gerrit](https://codereview.qt-project.org/) and add necessary
information to your account. Remember to accept
[Contributor License Agreement (CLA)](https://www.qt.io/community/legal-contribution-agreement-qt).

Configure Gerrit by following **How to get started - Gerrit registration**,
**Local Setup** and **Configuring Git** sections from the
[Setting up Gerrit](https://wiki.qt.io/Setting_up_Gerrit) wiki page.

After correct configuration you should see the following message
when trying `ssh codereview.qt-project.org` command:

```shell
  ****    Welcome to Gerrit Code Review    ****

  Hi <name>, you have successfully connected over SSH.

  Unfortunately, interactive shells are disabled.
  To clone a hosted Git repository, use:

  git clone ssh://<username>@codereview.qt-project.org:29418/qt/qtbridge-python.git

Connection to codereview.qt-project.org closed.
```

## Development setup

## Find something to work on

### Fix something you have discovered

If you've found a bug or have an idea for an improvement, feel free to
work on it directly. For larger changes, it's a good idea to open an issue
first to discuss it. See [Reporting Bugs](https://wiki.qt.io/Reporting_Bugs)
for more details.

### Picking an existing issue

If you're not working on something specific, check our
[Bug Report system](https://qt-project.atlassian.net/jira/software/c/projects/QTBRIDGES/components)
for open issues.

If you're unsure what to pick, feel free to ask on our
[Qt Bridges forum](https://forum.qt.io/category/78/qt-bridges) or join
[Qt Bridges Discord](https://discord.com/invite/WNdGHnHagP) - we're happy
to help you get started!

## Making changes

1. Create a new branch:

`git checkout -b feature-name`

2. Make your changes
3. Keep changes focused and minimal

## Commit and Push

Once you have your local patch ready to submit, check the
[Commit Policy](https://wiki.qt.io/Commit_Policy) and remember to add a
**Task-number:** or **Fixes:** entry to the commit footer.

Commit your changes:

```shell
git add <the files you modified>
git commit # this will open an editor, for you to write a commit message
git push origin HEAD:refs/for/dev
```

Your change will now appear in [Gerrit](https://codereview.qt-project.org/)
for review, where you will be able to modify the commit message, add reviewers
and view your change in detail.

## Reporting Bugs and Suggestions

If you're not contributing code, you can still help by reporting bugs or
suggesting features in our
[Bug Report system](https://qt-project.atlassian.net/jira/software/c/projects/QTBRIDGES/components).
When reporting an issue, please see
[Reporting Bugs](https://wiki.qt.io/Reporting_Bugs) first.

## Need Help?

If anything is unclear, don't worry - we're here to help!

Feel free to ask on our [Qt Bridges forum](https://forum.qt.io/category/78/qt-bridges),
join [Qt Bridges Discord](https://discord.com/invite/WNdGHnHagP) server or
get support from the community on other [Online communities](https://wiki.qt.io/Online_Communities).

Thanks again for contributing! ❤️
