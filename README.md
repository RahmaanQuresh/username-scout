# username-scout

Find out where a username exists across 15 public sites — in one command, with zero dependencies.

`username-scout` asks each site one simple question: *"does a profile with this handle exist?"* Use it to pick a handle for a new account, or to audit where your own name already appears.

## Quick start

Requires Python 3.9 or newer. Nothing to install.

```bash
python scout.py torvalds          # scan all 15 sites
python scout.py myhandle --json   # machine-readable output
python scout.py --list-sites      # show every supported site
```

## Example (real output)

```
$ python scout.py torvalds
Scanning 15 sites for 'torvalds'...

result  site          profile
found   GitHub        https://github.com/torvalds
found   Chess.com     https://www.chess.com/member/torvalds
found   Codewars      https://www.codewars.com/users/torvalds
 free   AtCoder       https://atcoder.jp/users/torvalds
found   RubyGems      https://rubygems.org/profiles/torvalds
found   Docker Hub    https://hub.docker.com/u/torvalds
found   Keybase       https://keybase.io/torvalds
found   SoundCloud    https://soundcloud.com/torvalds
 free   Vimeo         https://vimeo.com/torvalds
  ?     Flickr        https://www.flickr.com/people/torvalds
found   DeviantArt    https://www.deviantart.com/torvalds
found   Kaggle        https://www.kaggle.com/torvalds
 free   Gravatar      https://gravatar.com/torvalds
 free   WordPress     https://profiles.wordpress.org/torvalds/
 free   Blogger       https://torvalds.blogspot.com/

found = profile exists   free = username looks available
? = site blocked us or gave an odd answer   ! = could not reach site

9 found, 5 free, 1 unclear, 0 unreachable
```

A scan of a made-up username returns `0 found, 15 free, 0 unclear` — no false positives.

## How it works

For each site, `scout.py` requests the public profile URL and reads one thing: the HTTP status code.

- **200** → the profile exists (`found`)
- **404** → no such profile (`free`)
- **anything else** → reported as `unclear`, never guessed
- site unreachable → `!` (excluded from the verdict)

Results are hints, not proof — sites change their behavior, so open the profile link to confirm anything important.

## Why only 15 sites?

Every site on the list was **verified by hand**: it answers 200 for a real profile and 404 for a missing one. Popular OSINT lists include big networks like Reddit, Telegram, Medium, npm, and PyPI — but in testing, those sites either block automated checks or answer "yes" for usernames that don't exist. **A tool that lies is worse than a short list**, so they are excluded on purpose.

Excluded and why (checked 2026-09): Reddit and Medium block bots (403), npm's registry requires login, Telegram and PyPI answer 200 for anyone, GitLab and Hacker News rate-limit or redirect.

## Responsible use

This tool reads **no private data**, logs in to **nothing**, and bypasses **nothing** — it only notices whether a public profile page exists. Please use it the friendly way: choosing your own handle, checking your own footprint, or naming a project. Don't use it to profile or harass people, and respect each site's terms of service.

## Tests

The HTTP layer is injected, so all tests run offline:

```bash
python -m unittest discover tests
```

## Roadmap

- [ ] `--only` / `--exclude` flags to scan a subset of sites
- [ ] CSV export alongside `--json`
- [ ] Move the site list to a JSON file so people can add sites without touching code

Ideas and pull requests are welcome — the whole tool is one small file (`scout.py`).

## License

[MIT](LICENSE)
