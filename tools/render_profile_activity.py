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
    # Diagnostic for source parity; public SVG only, never logs credentials.
    try:
        import xml.etree.ElementTree as ET
        u=("https://github-stats-extended.vercel.app/api?username=Nahian2002"
           "&include_all_commits=true&show_icons=true"
           "&show=reviews,discussions_started,discussions_answered,prs_merged"
           "&theme=tokyonight&hide_border=true&hide_title=true&line_height=22")
        req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=25) as resp:
            raw=resp.read()
        root=ET.fromstring(raw)
        tokens=[(n.text or "").strip() for n in root.iter()
                if n.tag.rsplit("}",1)[-1] in ("text","tspan") and (n.text or "").strip()]
        print("DIAGNOSTIC provider SVG",len(raw),"label-value tokens",tokens[:70],flush=True)
    except Exception as e:
        print("DIAGNOSTIC provider unavailable",type(e).__name__,str(e)[:120],flush=True)
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
    return result

def fmt(value):
    return "—" if value is None else f"{value:,}"

def render(data):
    items=[
        ("STARS EARNED","stars","#68E7D6"),
        ("TOTAL COMMITS","commits","#F1F6FD"),
        ("PULL REQUESTS","pull_requests","#C8B6FF"),
        ("PRs MERGED","merged_prs","#82C2FD"),
        ("PRs REVIEWED","reviews","#F1F6FD"),
        ("ISSUES OPENED","issues","#F1F6FD"),
        ("DISCUSSIONS","discussions","#F1F6FD"),
        ("ACCEPTED ANSWERS","answers","#C8B6FF"),
        ("EXTERNAL REPOS","outside","#F1F6FD"),
    ]
    parts=[]
    for i,(label,key,color) in enumerate(items):
        x,y=31+(i%3)*279,88+(i//3)*101
        parts.append(f'<rect x="{x}" y="{y}" rx="11" width="267" height="93" fill="#132238" stroke="#233B58"/>')
        parts.append(f'<text x="{x+17}" y="{y+27}" font-size="17.5" fill="#A9BBD4">{label}</text>')
        parts.append(f'<text x="{x+17}" y="{y+73}" font-size="35" fill="{color}" font-weight="700">{escape(fmt(data[key]))}</text>')
    streaks=[
        ("TOTAL CONTRIBUTIONS","contributions","#82C2FD"),
        ("CURRENT STREAK","current_streak","#68E7D6"),
        ("LONGEST STREAK","longest_streak","#C8B6FF"),
    ]
    for i,(label,key,color) in enumerate(streaks):
        x,y=894,91+i*101
        parts.append(f'<rect x="{x}" y="{y}" rx="11" width="347" height="91" fill="#142139" stroke="#263D5D"/>')
        parts.append(f'<rect x="{x+1}" y="{y+14}" rx="2" width="4" height="61" fill="{color}"/>')
        parts.append(f'<text x="{x+22}" y="{y+27}" font-size="17.5" fill="#A9BBD4">{label}</text>')
        parts.append(f'<text x="{x+22}" y="{y+71}" font-size="38" fill="{color}" font-weight="700">{escape(fmt(data[key]))}</text>')
    updated=escape(data["updated"])
    result=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="432" viewBox="0 0 1280 432" role="img" aria-label="Live public GitHub activity for {USER}, updated {updated}">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0B1425"/><stop offset=".6" stop-color="#101C30"/><stop offset="1" stop-color="#131C32"/></linearGradient></defs>
<rect x="1" y="1" rx="17" width="1278" height="430" fill="url(#bg)" stroke="#365375" stroke-width="2"/>
<rect x="30" y="24" rx="2" width="5" height="33" fill="#63E9DA"/>
<g font-family="Arial,Helvetica,sans-serif">
<text x="49" y="49" font-size="27" fill="#F1F6FD" font-weight="700">THE LIVE SIGNAL</text>
<text x="1235" y="46" text-anchor="end" font-size="16" fill="#8FAAC7">GITHUB · UPDATED {updated}</text>
<path d="M31 70H1249" stroke="#324B67" stroke-width="1.2"/>
<rect x="878" y="84" rx="12" width="368" height="314" fill="#101C30" stroke="#304969"/>
{''.join(parts)}
<text x="38" y="414" font-size="15" fill="#829DB8">PUBLIC ACTIVITY · REGENERATED DAILY</text>
<text x="1240" y="414" text-anchor="end" font-size="15" fill="#94E9DB">BUILD / TEST / REFINE</text>
</g></svg>'''
    import xml.etree.ElementTree as ET
    ET.fromstring(result)
    if result.count('width="267"')!=9: raise AssertionError("Nine metric tiles required")
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
