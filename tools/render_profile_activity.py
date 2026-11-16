#!/usr/bin/env python3
"""Generate a daily, GitHub-native 1280x432 public activity panel.

Uses only the short-lived GITHUB_TOKEN from the profile repository's Actions.
Never fabricates numbers, never exposes credentials, and fails closed if GitHub
GraphQL can't supply required public activity. No third-party Python packages.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, timedelta, timezone
from html import escape
import json, os, pathlib, urllib.request

USER = "Nahian2002"
MIN_YEAR = 2022
API = "https://api.github.com/graphql"
BASE = """query($login:String!,$cursor:String) {
 user(login:$login) {
  login
  repositories(first:100,after:$cursor,ownerAffiliations:OWNER,privacy:PUBLIC) {
   nodes { stargazerCount } pageInfo { hasNextPage endCursor }
  }
  pullRequests(first:1) { totalCount }
  mergedPRs:pullRequests(first:1,states:[MERGED]) { totalCount }
  issues(first:1) { totalCount }
  repositoryDiscussions(first:1) { totalCount }
  repositoryDiscussionComments(first:1,onlyAnswers:true) { totalCount }
 }
}"""
YEAR = """query($login:String!,$from:DateTime!,$to:DateTime!) {
 user(login:$login) {
  contributionsCollection(from:$from,to:$to) {
   totalCommitContributions
   totalPullRequestReviewContributions
   contributionCalendar {
    weeks { contributionDays { date contributionCount } }
   }
  }
 }
}"""
OUTSIDE = """query($login:String!) {
 user(login:$login) {
  repositoriesContributedTo(first:1,includeUserRepositories:false) { totalCount }
 }
}"""

def gql(query, vars):
    token=os.getenv("GITHUB_TOKEN")
    if not token: raise RuntimeError("GITHUB_TOKEN missing: refuse unverified live statistics")
    body=json.dumps({"query":query,"variables":vars}).encode("utf-8")
    req=urllib.request.Request(API,body,headers={
        "Authorization":f"Bearer {token}",
        "User-Agent":"Nahian2002-profile-activity",
        "Content-Type":"application/json",
        "Accept":"application/vnd.github+json",
    },method="POST")
    with urllib.request.urlopen(req,timeout=35) as res: obj=json.load(res)
    if obj.get("errors") or not obj.get("data"):
        raise RuntimeError("GitHub GraphQL error: "+str(obj.get("errors"))[:500])
    return obj["data"]

def collect():
    first=gql(BASE,{"login":USER,"cursor":None})["user"]
    if not first or first["login"].lower()!=USER.lower(): raise ValueError("Incorrect GitHub user")
    r=first["repositories"]
    stars=0
    while True:
        stars+=sum(int(v["stargazerCount"]) for v in r["nodes"])
        if not r["pageInfo"]["hasNextPage"]: break
        r=gql(BASE,{"login":USER,"cursor":r["pageInfo"]["endCursor"]})["user"]["repositories"]
    now=datetime.now(timezone.utc)
    today=now.date()
    days={}
    commits=reviews=0
    for year in range(MIN_YEAR,today.year+1):
        a=datetime(year,1,1,tzinfo=timezone.utc)
        b=min(now,datetime(year+1,1,1,tzinfo=timezone.utc)-timedelta(seconds=1))
        obj=gql(YEAR,{"login":USER,
            "from":a.isoformat().replace("+00:00","Z"),
            "to":b.isoformat().replace("+00:00","Z")})["user"]["contributionsCollection"]
        commits+=int(obj["totalCommitContributions"])
        reviews+=int(obj["totalPullRequestReviewContributions"])
        for week in obj["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                day=date.fromisoformat(d["date"])
                if a.date()<=day<=today: days[day]=int(d["contributionCount"])
    longest=run=0
    d=date(MIN_YEAR,1,1)
    while d<=today:
        run=run+1 if days.get(d,0)>0 else 0
        longest=max(longest,run)
        d+=timedelta(days=1)
    d=today if days.get(today,0)>0 else today-timedelta(days=1)
    current=0
    while d>=date(MIN_YEAR,1,1) and days.get(d,0)>0:
        current+=1
        d-=timedelta(days=1)
    try:
        # Independent optional query: permission failure must not invent a count.
        outside=int(gql(OUTSIDE,{"login":USER})["user"]["repositoriesContributedTo"]["totalCount"])
    except Exception as e:
        print("NOTICE external-repository metric unavailable:",type(e).__name__,flush=True)
        outside=None
    result={
        "stars":stars,"commits":commits,
        "pull_requests":int(first["pullRequests"]["totalCount"]),
        "merged_prs":int(first["mergedPRs"]["totalCount"]),
        "reviews":reviews,
        "issues":int(first["issues"]["totalCount"]),
        "discussions":int(first["repositoryDiscussions"]["totalCount"]),
        "answers":int(first["repositoryDiscussionComments"]["totalCount"]),
        "outside":outside,"contributions":sum(days.values()),
        "current_streak":current,"longest_streak":longest,
        "updated":today.isoformat(),
    }
    for k,v in result.items():
        if k!="updated" and v is not None and (type(v)!=int or v<0):
            raise ValueError("Bad GitHub number for "+k)

    # Preserve the *same* metric definitions/formatting as the live GitHub
    # Stats Extended card already used in this profile (including B+ rank).
    import re
    import xml.etree.ElementTree as ET
    source=("https://github-stats-extended.vercel.app/api?username=Nahian2002"
            "&include_all_commits=true&show_icons=true"
            "&show=reviews,discussions_started,discussions_answered,prs_merged"
            "&theme=tokyonight&hide_border=true&hide_title=true&line_height=22")
    with urllib.request.urlopen(
        urllib.request.Request(source,headers={"User-Agent":"Mozilla/5.0"}),
        timeout=30
    ) as stream:
        raw=stream.read()
    if len(raw)<500 or len(raw)>300000:
        raise RuntimeError("Invalid GitHub Stats Extended response length")
    root=ET.fromstring(raw)
    tokens=[(n.text or "").strip() for n in root.iter()
            if n.tag.rsplit("}",1)[-1] in ("text","tspan") and (n.text or "").strip()]
    expected={
        "stars":"Total Stars Earned:",
        "commits":"Total Commits:",
        "pull_requests":"Total PRs:",
        "merged_prs":"Total PRs Merged:",
        "reviews":"Total PRs Reviewed:",
        "issues":"Total Issues:",
        "discussions":"Total Discussions Started:",
        "answers":"Total Discussions Answered:",
        "outside":"Contributed to (last year):",
    }
    for key,label in expected.items():
        if tokens.count(label)!=1:
            raise RuntimeError("Missing/duplicate live stats label: "+label)
        value=tokens[tokens.index(label)+1].strip()
        if not re.fullmatch(r"\d[\d,.]*[kKmM]?",value):
            raise RuntimeError("Unexpected live stats value for "+label)
        result[key]=value
    rank=tokens[0] if tokens else ""
    if not re.fullmatch(r"[A-S][+-]?",rank):
        raise RuntimeError("Unrecognized GitHub Stats Extended rank")
    result["rank"]=rank

    # Match the exact current/longest streak and lifetime contributions
    # shown by the already-used DemoLab card. Treat missing/changed markup as
    # a refresh failure: retain the previously published SVG.
    u=("https://streak-stats.demolab.com/?user=Nahian2002"
       "&theme=tokyonight&hide_border=true&background=0B1120"
       "&ring=66E3D3&fire=A18CFF&currStreakLabel=66E3D3")
    with urllib.request.urlopen(
        urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30
    ) as resp:
        sr=ET.fromstring(resp.read())
    st=[(node.text or "").strip() for node in sr.iter()
        if node.tag.rsplit("}",1)[-1] in ("text","tspan") and (node.text or "").strip()]
    for name in ("Total Contributions","Current Streak","Longest Streak"):
        if st.count(name)!=1:
            raise RuntimeError("Unrecognized DemoLab streak label "+name)
    total_idx=st.index("Total Contributions")
    current_idx=st.index("Current Streak")
    longest_idx=st.index("Longest Streak")
    streak_values={
        "contributions":st[total_idx-1],
        "current_streak":st[current_idx+2],
        "longest_streak":st[longest_idx-1],
    }
    for name,value in streak_values.items():
        if not re.fullmatch(r"\d[\d,]*",value):
            raise RuntimeError("Invalid streak numeric value for "+name)
        result[name]=value
    print("SOURCE CHECK: both GitHub Stats Extended and DemoLab live metrics verified",flush=True)
    return result

def fmt(value):
    return "—" if value is None else str(value) if isinstance(value,str) else f"{value:,}"

def render(data):
    """Editorial hierarchy rather than a dense mini-card analytics grid.

    Four lead numbers are genuinely readable on a normal GitHub profile
    column; every other stat is present in a calmer two-row detail strip.
    No metric is dropped, recalculated, or hardcoded.
    """
    primary = [
        ("TOTAL COMMITS", "commits", "#F2F7FF"),
        ("CONTRIBUTIONS", "contributions", "#83C3FF"),
        ("CURRENT STREAK", "current_streak", "#65E9D5"),
        ("PULL REQUESTS", "pull_requests", "#BCA7FF"),
    ]
    secondary = [
        ("STARS EARNED", "stars", "#66E8D8"),
        ("PRs MERGED", "merged_prs", "#BCA7FF"),
        ("PRs REVIEWED", "reviews", "#EFF5FF"),
        ("ISSUES OPENED", "issues", "#EFF5FF"),
        ("DISCUSSIONS STARTED", "discussions", "#EFF5FF"),
        ("DISCUSSIONS ANSWERED", "answers", "#BCA7FF"),
        ("CONTRIBUTED (1Y)", "outside", "#EFF5FF"),
        ("LONGEST STREAK", "longest_streak", "#83C3FF"),
    ]
    keys = [x[1] for x in primary + secondary]
    expected = ("stars", "commits", "pull_requests", "merged_prs",
                "reviews", "issues", "discussions", "answers",
                "outside", "contributions", "current_streak", "longest_streak")
    if len(keys) != len(set(keys)) or set(keys) != set(expected):
        raise AssertionError("All 12 activity metrics must be displayed once")

    blocks = []
    # Primary strip: one shared surface with breathing room and slim dividers.
    for i, (label, key, color) in enumerate(primary):
        x = 55 + i * 302
        blocks.append(
            f'<g data-key="{key}">'
            f'<rect x="{x}" y="121" width="36" height="4" rx="2" fill="{color}"/>'
            f'<text x="{x}" y="156" font-size="21" fill="#A7BBD5" letter-spacing=".8">{escape(label)}</text>'
            f'<text x="{x}" y="224" font-size="59" font-weight="750" letter-spacing="-1.5" fill="{color}">{escape(fmt(data[key]))}</text>'
            '</g>'
        )
        if i:
            divider_x = x - 26
            blocks.append(
                f'<path d="M{divider_x} 127V228" stroke="#304760" stroke-width="1.5" opacity=".85"/>'
            )

    # Secondary strip: 8 complete metrics; no repetitive boxed widgets.
    for i, (label, key, color) in enumerate(secondary):
        row, col = divmod(i, 4)
        x = 55 + col * 302
        ly = 323 + row * 92
        vy = 366 + row * 92
        blocks.append(
            f'<g data-key="{key}">'
            f'<text x="{x}" y="{ly}" font-size="20" fill="#9FB3D0" letter-spacing=".3">{escape(label)}</text>'
            f'<text x="{x}" y="{vy}" font-size="36" font-weight="700" fill="{color}">{escape(fmt(data[key]))}</text>'
            '</g>'
        )
        if col:
            divider_x = x - 26
            blocks.append(
                f'<path d="M{divider_x} {ly-23}V{vy+5}" stroke="#29415A" stroke-width="1" opacity=".65"/>'
            )

    updated = escape(data["updated"])
    rank = escape(str(data["rank"]))
    result = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="500" viewBox="0 0 1280 500" role="img" aria-label="Daily GitHub activity for {USER}: all 12 metrics and rank, last updated {updated}">
<defs>
  <linearGradient id="panel" x1="0" y1="0" x2="1" y2="1">
    <stop stop-color="#0C182A"/><stop offset=".56" stop-color="#12233C"/>
    <stop offset="1" stop-color="#111D31"/>
  </linearGradient>
  <linearGradient id="accent" x1="0" x2="1">
    <stop stop-color="#62E6D5"/><stop offset="1" stop-color="#A58EFA"/>
  </linearGradient>
</defs>
<rect x="1" y="1" width="1278" height="498" rx="17" fill="url(#panel)" stroke="#355577" stroke-width="2"/>
<path d="M23 1H1257" stroke="url(#accent)" stroke-width="2" opacity=".45"/>
<g font-family="Arial,Helvetica,sans-serif">
  <rect x="38" y="30" width="5" height="31" rx="2.5" fill="#65E9D5"/>
  <text x="58" y="56" font-size="31" font-weight="800" letter-spacing=".25" fill="#F5F8FF">GITHUB ACTIVITY</text>
  <rect x="365" y="30" width="104" height="31" rx="15.5" fill="#242744" stroke="#5B5D91"/>
  <text x="417" y="51" text-anchor="middle" font-size="19" font-weight="750" fill="#C4B2FF">RANK {rank}</text>
  <text x="1242" y="53" text-anchor="end" font-size="18" fill="#93ACC8">UPDATED {updated}</text>
  <path d="M38 80H1242" stroke="#37506A" stroke-width="1.3"/>

  <rect x="36" y="100" width="1208" height="151" rx="14" fill="#172841" opacity=".64"/>
  {''.join(blocks[:7])}
  <path d="M38 269H1242" stroke="#37506A" stroke-width="1.1"/>
  <text x="54" y="292" font-size="18" letter-spacing="1.6" fill="#65E9D5" font-weight="700">THE REST OF THE STORY</text>
  {''.join(blocks[7:])}

  <path d="M38 476H1242" stroke="#30465E" stroke-width="1"/>
  <text x="43" y="493" font-size="15" fill="#8FA8C4">LIVE METRICS · UPDATED AUTOMATICALLY</text>
  <text x="1238" y="493" text-anchor="end" font-size="15" fill="#76E1D3">BUILD / TEST / REFINE</text>
</g>
</svg>'''
    import xml.etree.ElementTree as ET
    ET.fromstring(result)
    for key in expected:
        if result.count(f'data-key="{key}"') != 1:
            raise AssertionError("Missing, duplicated or altered metric: " + key)
    if "RANK " + rank not in result:
        raise AssertionError("Provider rank not rendered")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="assets/github-activity-live.svg")
    args=p.parse_args()
    data=collect()
    file=pathlib.Path(args.output)
    file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(render(data),encoding="utf-8")
    print(f"PASS live public activity: {data}",flush=True)
