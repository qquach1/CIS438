#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The headline numbers and the seven tabs. Each render_* function draws from an already-filtered slice."""

from http import HTTPStatus

import pandas as pd
import streamlit as st

from charts import (DAY_LABELS, bubble_map, columns, daily_trend, heatmap, line, palette, ranked_bars,
                    segmented_bar, stacked_columns)
from data_loader import AI_AGENTS, COLUMN_NOTES, SEGMENTS, STATUS_LABELS, engagement_segments, segment, site_kpis

DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DEVICES = ['Desktop', 'Bot', 'Mobile', 'Tablet', 'Other']
TILE = dict(border=True, width=180)


def tiles():
    """A row of stat tiles. Fixed-width tiles wrap onto a second row instead of squeezing their numbers."""
    return st.container(horizontal=True, gap="small", horizontal_alignment="distribute")


def status_meaning(code):
    if code == 499:
        return "Client Closed Request"  # nginx's code for a visitor who gave up waiting
    try:
        return HTTPStatus(code).phrase
    except ValueError:
        return ""


def show(key, fig):
    """Draw a Plotly figure. Its own key keeps two identical charts (a one-section filter, say) apart.

    Scroll-zoom is off so scrolling the page over a chart (the map especially) scrolls the page.
    """
    st.plotly_chart(fig, key=key, config={"scrollZoom": False})


def every_month(series, fill=0):
    """Reindex a by-month series to every month from its first to its last, so quiet months aren't skipped."""
    if series.empty:
        return series
    months = pd.period_range(series.index.min(), series.index.max(), freq='M').astype(str)
    return series.reindex(months, fill_value=fill)


def nothing_here():
    st.info("Nothing matches the filters. Widen the dates or clear the sections in the sidebar.",
            icon=":material/filter_alt_off:")


def counts_by(df, key):
    """Requests and distinct visitors per value of key, busiest first."""
    return (df.groupby(key).agg(requests=('ip', 'size'), visitors=('ip', 'nunique'))
            .sort_values('requests', ascending=False))


def hits_bars(table, c, noun, labels=None):
    """Ranked bars of a counts_by() table, with the full name and visitors in the hover."""
    labels = table.index if labels is None else labels
    custom = [[str(name), visitors] for name, visitors in zip(labels, table['visitors'])]
    hover = "<b>%{customdata[0]}</b><br>%{x:,} " + noun + " · %{customdata[1]:,} visitors<extra></extra>"
    return ranked_bars(labels, table['requests'], c, hover, customdata=custom)


def most_common(df, col):
    """Each IP's most frequent value of col."""
    counts = df.groupby(['ip', col]).size().reset_index(name='n').sort_values('n')
    return counts.drop_duplicates('ip', keep='last').set_index('ip')[col]


def size_unit(values):
    """GB once the biggest value reaches a gigabyte, MB below that. Returns (scaled values, unit)."""
    return (values / 1e9, "GB") if values.max() >= 1e9 else (values / 1e6, "MB")


# ── Headline numbers (notebook section 7) ────────────────────────────────────

def render_kpis(df):
    k = site_kpis(df)
    by_month = every_month(df.groupby('month').agg(
        requests=('ip', 'size'), visitors=('ip', 'nunique'), bytes=('size', 'sum'),
        errors=('status', lambda s: (s >= 400).mean()), bots=('is_bot', 'mean')))
    by_month[['errors', 'bots']] = by_month[['errors', 'bots']].where(by_month['requests'] > 0)  # no rate, not 0%
    specs = [
        ("Total requests", f"{k['total_requests']:,}", by_month['requests'], "bar",
         "Every line in the log for these dates: pages, CSS, JS, images and crawlers."),
        ("Unique visitors", f"{k['unique_visitors']:,}", by_month['visitors'], "bar",
         "Distinct IP addresses. People on one network share an address, so this undercounts people."),
        ("Bandwidth", f"{k['bandwidth_gb']:.2f} GB", by_month['bytes'] / 1e9, "bar",
         "Bytes the server sent back, added up."),
        ("Error rate", f"{k['error_rate']:.1%}", by_month['errors'], "line",
         "Share of requests answered with a 4xx or 5xx status."),
        ("Bot traffic", f"{k['bot_pct']:.1%}", by_month['bots'], "line",
         "Share of requests whose user agent names a crawler (bot, spider, Googlebot, bingbot …)."),
    ]
    with tiles():
        for label, value, trend, kind, help_text in specs:
            st.metric(label, value, help=f"{help_text} The sparkline has one point per month.",
                      chart_data=trend.round(6).tolist(), chart_type=kind, delta_color="off", **TILE)


# ── Traffic tab (notebook 8a and 8d) ─────────────────────────────────────────

def render_traffic(view, f):
    c = palette()
    if view.empty:
        return nothing_here()

    daily = view.groupby('date').size()
    daily.index = pd.to_datetime(daily.index)
    daily = daily.asfreq('D', fill_value=0)  # days without a request count as zero
    active = int((daily > 0).sum())
    busiest = daily.idxmax()
    peak_hour = int(view.groupby('hour').size().idxmax())
    peak_day = DAY_NAMES[int(view.groupby('day_of_week').size().idxmax())]

    with tiles():
        st.metric(f.noun.capitalize(), f"{len(view):,}", help=f"{f.traffic}: {f.description.lower()}.", **TILE)
        st.metric("Per active day", f"{len(view) / active:,.0f}", **TILE,
                  help=f"Average over the {active:,} days with at least one request, out of {len(daily):,} days.")
        st.metric("Busiest day", f"{daily.max():,}", delta=f"{busiest:%a, %b} {busiest.day}, {busiest.year}",
                  delta_color="off", delta_arrow="off", help=f"The most {f.noun} on a single day.", **TILE)
        st.metric("Peak hour", f"{peak_hour:02d}:00", delta=f"{peak_day}s busiest", delta_color="off",
                  delta_arrow="off", help=f"Hour of day with the most {f.noun}, in {f.clock_label}.", **TILE)

    # One busy day (a class using the site, say) can flatten everything else; a log scale spreads it out
    active_days = daily[daily > 0]
    lopsided = len(active_days) > 1 and daily.max() > 20 * active_days.median()
    log = st.toggle("Log scale", key="traffic_log",
                    help="Spreads out the quiet stretches when a few busy days or hours dwarf the rest. "
                         "Applies to both charts on this tab.")

    st.subheader(f"Daily {f.noun}")
    show("traffic_daily", daily_trend(daily, c, f.noun, log=log))
    hint = " One day dwarfs the rest here; turn on **Log scale** to compare the others." if lopsided and not log else ""
    st.caption(f"Gray is each day ({f.clock_label}), blue the 7-day average. Days with none count as zero.{hint}")
    with st.expander("Daily counts as a table"):
        table = daily.rename_axis('Date').reset_index(name=f.noun.capitalize())
        st.dataframe(table, hide_index=True,
                     column_config={'Date': st.column_config.DateColumn(format="ddd, MMM D, YYYY")})

    st.subheader("Day of week by hour")
    grid = (view.groupby(['day_of_week', 'hour']).size().unstack(fill_value=0)
            .reindex(index=range(7), columns=range(24), fill_value=0))
    show("traffic_heatmap", heatmap(grid, c, f.clock_label, log=log))
    shade = "Brighter" if c["dark"] else "Darker"
    note = "" if f.server_clock else " Set the clock to server time in the sidebar to read them as the server's local hours."
    st.caption(f"{shade} cells had more {f.noun}. Hours are {f.clock_label}.{note}")
    with st.expander("Heatmap as a table"):
        st.dataframe(grid.set_axis(DAY_LABELS).rename(columns=lambda h: f"{h:02d}"))


# ── Pages tab (notebook 8c) ──────────────────────────────────────────────────

def render_pages(view, f):
    c = palette()
    if view.empty:
        return nothing_here()

    pages = counts_by(view, 'path')
    col1, col2 = st.columns((1.5, 1), gap="large")
    with col1:
        st.subheader("Top 10 pages")
        show("pages_top", hits_bars(pages.head(10), c, f.noun))
        st.caption(f"Ranked by {f.noun}. Query strings are dropped, so /page?x=1 counts as /page.")
    with col2:
        st.subheader("Sections")
        show("pages_sections", hits_bars(counts_by(view, 'section').head(10), c, f.noun))
        st.caption("First part of the URL path, such as /course or /account.")

    col3, col4 = st.columns((1.5, 1), gap="large")
    with col3:
        st.subheader("Courses")
        courses = counts_by(view.dropna(subset=['course']), 'course')
        if courses.empty:
            st.caption("No course pages in this slice.")
        else:
            show("pages_courses", hits_bars(courses, c, f.noun, labels=courses.index.str.upper()))
            st.caption("Requests whose URL names a course, such as /course/cis511/syllabus or /gba411/content/lectures.")
    with col4:
        st.subheader("Where requests come from")
        kinds = view['referer_type'].value_counts()
        st.html(segmented_bar([("Internal", int(kinds.get("Internal", 0)), c["accent"]),
                               ("Direct", int(kinds.get("Direct", 0)), c["aqua"]),
                               ("External", int(kinds.get("External", 0)), c["yellow"])], c, "Referrer"))
        st.caption("**Internal:** a link or script on the site itself. **Direct:** no referrer (typed, "
                   "bookmarked or an app). **External:** another website.")
        external = counts_by(view[view['referer_type'] == 'External'], 'referer_host').head(10)
        if not external.empty:
            st.dataframe(external.rename_axis('Referring site').reset_index(), hide_index=True, column_config={
                'requests': st.column_config.NumberColumn("Requests", format="localized"),
                'visitors': st.column_config.NumberColumn("Visitors", format="localized")})

    with st.expander(f"All {len(pages):,} pages"):
        st.dataframe(pages.assign(share=pages['requests'] / len(view) * 100).rename_axis('Page').reset_index(),
                     hide_index=True, column_config={
                         'requests': st.column_config.NumberColumn(f.noun.capitalize(), format="localized"),
                         'visitors': st.column_config.NumberColumn("Visitors", format="localized"),
                         'share': st.column_config.NumberColumn("Share", format="%.1f%%")})


# ── Visitors tab (notebook section 9) ────────────────────────────────────────

def render_visitors(view, f, geo_ok):
    c = palette()
    if view.empty:
        return nothing_here()

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Engagement segments")
        seg = engagement_segments(view)
        total = max(seg['visitors'].sum(), 1)
        show("visitors_segments", columns(seg['segment'], seg['visitors'], c,
                                "%{x}: %{y:,} visitors (%{customdata:.0%})<extra></extra>",
                                customdata=seg['visitors'] / total,
                                text=[f"{v:,} ({v / total:.0%})" for v in seg['visitors']]))
        rules = " · ".join(f"**{name}** {rule}" for name, rule in SEGMENTS.items())
        st.caption(f"Visitors (IPs) by how many {f.noun} each made: {rules}.")
    with col2:
        st.subheader("Devices")
        devices = view['device'].replace({'Unknown': 'Other'}).value_counts()
        colors = dict(Desktop=c["accent"], Bot=c["bot"], Mobile=c["aqua"], Tablet=c["yellow"], Other=c["gray"])
        st.html(segmented_bar([(d, int(devices.get(d, 0)), colors[d]) for d in DEVICES], c, "Devices"))
        b1, b2 = st.columns(2)
        for box, col, title in ((b1, 'browser', "Browsers"), (b2, 'os', "Operating systems")):
            with box:
                st.markdown(f"**{title}**")
                show(f"visitors_{col}", hits_bars(counts_by(view, col).head(6), c, f.noun))
        st.caption("Other: scripts and tools that don't say what they run on.")

    st.subheader("Where visitors are")
    if not geo_ok:
        st.info("The map needs the maxminddb package (`pip install maxminddb`) and GeoLite2-City.mmdb "
                "in the app's folder.", icon=":material/map:")
    else:
        located = view.dropna(subset=['latitude', 'longitude'])
        place = (located['city'] + ", " + located['country']).fillna(located['country'])
        places = (located.assign(place=place).groupby(['place', 'latitude', 'longitude'])
                  .agg(requests=('ip', 'size'), visitors=('ip', 'nunique')).reset_index()
                  .sort_values('requests', ascending=False))  # big bubbles first, so small ones sit on top
        m1, m2 = st.columns((1.7, 1), gap="large")
        with m1:
            if places.empty:
                st.caption("None of these requests came from an address with a known location.")
            else:
                show("visitors_map", bubble_map(places, c))
            private = int((view['country'] == 'Private network').sum())
            note = (f" {private:,} {f.noun} came from a private address on the server's own network "
                    f"(192.168.x.x), which has no location." if private else "")
            st.caption(f"One bubble per city; its area grows with {f.noun}.{note}")
        with m2:
            st.markdown("**Top countries**")
            countries = counts_by(located, 'country').head(10)
            if not countries.empty:
                show("visitors_countries", hits_bars(countries, c, f.noun))

    st.subheader("Top visitors")
    who = (view.groupby('ip').agg(requests=('ip', 'size'), days=('date', 'nunique'), first=('date', 'min'),
                                  last=('date', 'max'), country=('country', 'first'), city=('city', 'first'))
           .sort_values('requests', ascending=False))
    who.insert(1, 'segment', who['requests'].map(segment))
    who['browser'] = most_common(view, 'browser')
    who['device'] = most_common(view, 'device')
    st.dataframe(who.rename_axis('IP').reset_index(), hide_index=True, placeholder="—", column_config={
        'requests': st.column_config.NumberColumn(f.noun.capitalize(), format="localized"),
        'segment': "Segment",
        'days': st.column_config.NumberColumn("Active days", help="Days with at least one request."),
        'first': st.column_config.DateColumn("First seen"),
        'last': st.column_config.DateColumn("Last seen"),
        'country': "Country", 'city': "City", 'browser': "Browser", 'device': "Device"})


# ── Server health tab (notebook 8b, 8f and 8g) ───────────────────────────────

def render_server(df):
    c = palette()
    st.caption("Every request in the selected dates, static files and crawlers included, so the Traffic "
               "setting doesn't apply here.")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Response status")
        cats = df['status_cat'].value_counts()
        parts = [("2xx Success", c["good"]), ("3xx Redirect", c["neutral"]),
                 ("4xx Client Err", c["warning"]), ("5xx Server Err", c["critical"])]
        st.html(segmented_bar([(name, int(cats.get(name, 0)), color) for name, color in parts], c,
                              "Response status"))
        codes = df.groupby('status').size().rename('requests').reset_index()
        codes.insert(1, 'meaning', codes['status'].map(status_meaning))
        codes['share'] = codes['requests'] / len(df) * 100
        st.dataframe(codes, hide_index=True, column_config={
            'status': st.column_config.NumberColumn("Status", format="%d"), 'meaning': "Meaning",
            'requests': st.column_config.NumberColumn("Requests", format="localized"),
            'share': st.column_config.NumberColumn("Share", format="%.1f%%")})
        st.caption("304 Not Modified means the browser already had the file cached, so nothing was resent.")
    with col2:
        st.subheader("Error rate by month")
        rate = every_month(df.groupby('month')['status'].agg(lambda s: (s >= 400).mean()), fill=None)
        show("server_error_rate", line(rate.index, rate.values, c, "%{x}: %{y:.1%} of requests<extra></extra>",
                                       yformat=".0%"))
        gaps = " Gaps are months with no requests in the log." if rate.isna().any() else ""
        st.caption(f"Share of each month's requests answered with a 4xx or 5xx status.{gaps}")

    col3, col4 = st.columns(2, gap="large")
    with col3:
        st.subheader("Top 10 error URLs")
        errors = df[df['status'] >= 400].groupby(['path', 'status']).size().nlargest(10)
        if errors.empty:
            st.caption("No errors in these dates.")
        else:
            pairs = list(errors.index)
            server_side = [status >= 500 for _, status in pairs]
            show("server_error_urls", ranked_bars(
                [f"{status} {path}" for path, status in pairs], errors.values, c,
                "<b>%{customdata[0]}</b><br>%{customdata[1]} · %{x:,} times<extra></extra>",
                customdata=[[path, f"{status} {status_meaning(status)}"] for path, status in pairs],
                colors=[c["critical"] if s else c["warning"] for s in server_side],
                names=["5xx server error" if s else "4xx client error" for s in server_side]))
            st.caption("Each bar is one URL and the status it got back.")
    with col4:
        bandwidth, unit = size_unit(every_month(df.groupby('month')['size'].sum()))
        st.subheader("Bandwidth by month")
        show("server_bandwidth", columns(bandwidth.index, bandwidth.values, c,
                                "%{x}: %{y:,.2f} " + unit + "<extra></extra>", ytitle=f"{unit} served"))
        st.caption("Bytes sent back each month. CSS, JS and images make up most of it.")

    st.subheader("Vulnerability probes")
    probes = df[df['is_probe']]
    if probes.empty:
        st.caption("No probes in these dates.")
        return
    with tiles():
        st.metric("Probe requests", f"{len(probes):,}", **TILE)
        st.metric("Probing IPs", f"{probes['ip'].nunique():,}", **TILE)
        st.metric("Answered 404", f"{(probes['status'] == 404).mean():.0%}", **TILE,
                  help="Share of probes that found nothing because the site doesn't run that software.")
    p1, p2 = st.columns((1, 1.2), gap="large")
    with p1:
        st.markdown("**Most probed paths**")
        show("server_probe_paths", hits_bars(counts_by(probes, 'path').head(8), c, "requests"))
    with p2:
        st.markdown("**Who is probing**")
        scanners = (probes.groupby('ip').agg(requests=('ip', 'size'), paths=('path', 'nunique'),
                                             country=('country', 'first'), first=('date', 'min'),
                                             last=('date', 'max'))
                    .sort_values('requests', ascending=False))
        st.dataframe(scanners.rename_axis('IP').reset_index(), hide_index=True, placeholder="—", column_config={
            'requests': st.column_config.NumberColumn("Requests", format="localized", width="small"),
            'paths': st.column_config.NumberColumn("Paths tried", width="small"), 'country': "Country",
            'first': st.column_config.DateColumn("First seen"), 'last': st.column_config.DateColumn("Last seen")})
    st.caption("Requests for software this site doesn't run, such as WordPress (wp-login.php), PHP pages and "
               "leaked secrets (.env, .git/config). Automated scanners try them on every server they find.")


# ── Bots tab (notebook 8e) ───────────────────────────────────────────────────

def render_bots(df, df_pages):
    c = palette()
    st.caption("Crawlers included by definition, so the Traffic setting doesn't apply here.")
    bot_pages = df_pages[df_pages['is_bot']]
    bots = df[df['is_bot']]

    with tiles():
        st.metric("Bot page requests", f"{len(bot_pages):,}", **TILE)
        st.metric("Bot share of pages", f"{len(bot_pages) / max(len(df_pages), 1):.1%}", **TILE,
                  help="Of all content-page requests (no CSS, JS or images), the share made by crawlers.")
        st.metric("Crawlers seen", f"{bots['crawler'].nunique():,}", **TILE)
        st.metric("Crawler IPs", f"{bots['ip'].nunique():,}", **TILE)

    st.subheader("Bot vs human page requests")
    st.html(segmented_bar([("Human", len(df_pages) - len(bot_pages), c["human"]),
                           ("Bot", len(bot_pages), c["bot"])], c, "Content-page requests"))

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.subheader("Top crawlers")
        if bots.empty:
            st.caption("No crawlers in these dates.")
        else:
            crawlers = counts_by(bots, 'crawler').head(10).rename(columns={'visitors': 'ips'})
            custom = [[name, ips] for name, ips in zip(crawlers.index, crawlers['ips'])]
            show("bots_crawlers", ranked_bars(crawlers.index, crawlers['requests'], c,
                                        "<b>%{customdata[0]}</b><br>%{x:,} requests from "
                                        "%{customdata[1]:,} IPs<extra></extra>", customdata=custom))
            st.caption("Every request each crawler made, static files included.")
    with col2:
        st.subheader("Page requests by month")
        monthly = every_month(df_pages.groupby(['month', 'is_bot']).size().unstack(fill_value=0)
                              .reindex(columns=[False, True], fill_value=0))
        show("bots_monthly", stacked_columns(monthly.index, [("Human", monthly[False], c["human"]),
                                                        ("Bot", monthly[True], c["bot"])], c))

    col3, col4 = st.columns(2, gap="large")
    with col3:
        st.subheader("What crawlers read")
        if bot_pages.empty:
            st.caption("No crawler page requests in these dates.")
        else:
            show("bots_sections", hits_bars(counts_by(bot_pages, 'section').head(8), c, "requests"))
            st.caption("Sections crawlers asked for most.")
    with col4:
        st.subheader("Scripts the bot rule misses")
        scripts = counts_by(df[df['is_script']], 'user_agent').rename(columns={'visitors': 'ips'})
        if scripts.empty:
            st.caption("None in these dates.")
        else:
            st.dataframe(scripts.rename_axis('User agent').reset_index(), hide_index=True,
                         column_order=['requests', 'ips', 'User agent'], column_config={
                             'requests': st.column_config.NumberColumn("Requests", format="localized", width="small"),
                             'ips': st.column_config.NumberColumn("IPs", width="small")})
            st.caption(f"Command-line tools and headless browsers are automated too, but their user agents don't "
                       f"say bot, so BOT_PATTERNS counts their {scripts['requests'].sum():,} requests as human.")


# ── AI tools tab ─────────────────────────────────────────────────────────────

def render_ai_tools(df, site):
    c = palette()
    st.subheader(f"The ChatGPT tool on {site}")
    ai = df[df['ai_page'].notna()]
    if ai.empty:
        st.info("No requests to the site's ChatGPT pages in these dates.", icon=":material/chat:")
    else:
        with tiles():
            st.metric("Requests", f"{len(ai):,}", **TILE,
                      help="The ChatGPT pages plus everything fetched while one was open: the chat's socket.io "
                           "traffic, scripts and styles.")
            st.metric("Visitors", f"{ai['ip'].nunique():,}", **TILE)
            st.metric("Days used", f"{ai['date'].nunique():,}", **TILE)
            st.metric("Courses", f"{ai.loc[ai['ai_course'] != 'general', 'ai_course'].nunique():,}", **TILE,
                      help="Courses whose ChatGPT page was used. The general page belongs to no course.")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown("**By course**")
            by_course = counts_by(ai, 'ai_course')
            labels = [("General (no course)" if code == "general" else code.upper()) for code in by_course.index]
            show("ai_by_course", hits_bars(by_course, c, "requests", labels=labels))
        with col2:
            st.markdown("**By month**")
            months = every_month(ai.groupby('month').size())
            show("ai_by_month", columns(months.index, months.values, c, "%{x}: %{y:,} requests<extra></extra>"))
        pages = ai.groupby('ai_page').agg(
            requests=('ip', 'size'), visitors=('ip', 'nunique'),
            posts=('method', lambda m: int((m == 'POST').sum())), first=('date', 'min'), last=('date', 'max'),
        ).sort_values('requests', ascending=False)
        st.dataframe(pages.rename_axis('ChatGPT page').reset_index(), hide_index=True, column_config={
            'requests': st.column_config.NumberColumn("Requests", format="localized"),
            'visitors': st.column_config.NumberColumn("Visitors"),
            'posts': st.column_config.NumberColumn("POSTs", help="Data sent up from the page, mostly the chat's "
                                                                  "socket.io traffic: messages plus keep-alives."),
            'first': st.column_config.DateColumn("First used"), 'last': st.column_config.DateColumn("Last used")})
        st.caption("The chat runs over socket.io, which the notebook counts as a static file. Its requests carry "
                   "the ChatGPT page as their referrer, which is why this tab reads every request.")

    st.subheader("AI assistants and crawlers")
    agents = df[df['ai_agent'].notna()]
    if agents.empty:
        st.info(f"None of the {len(AI_AGENTS)} AI crawlers and assistants this tab looks for (GPTBot, ChatGPT-User, "
                f"ClaudeBot, PerplexityBot …) show up in these dates.", icon=":material/smart_toy:")
    else:
        with tiles():
            st.metric("Requests", f"{len(agents):,}", **TILE)
            st.metric("Agents", f"{agents['ai_agent'].nunique():,}", **TILE)
            st.metric("Companies", f"{agents['ai_company'].nunique():,}", **TILE)
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown("**By agent**")
            by_agent = counts_by(agents, 'ai_agent')
            labels = [f"{name} · {AI_AGENTS[name]}" for name in by_agent.index]
            show("ai_by_agent", hits_bars(by_agent, c, "requests", labels=labels))
        with col2:
            st.markdown("**Pages they read most**")
            show("ai_agent_pages", hits_bars(counts_by(agents, 'path').head(8), c, "requests"))
    with st.expander("AI agents this tab looks for"):
        st.dataframe(pd.DataFrame({'Agent': list(AI_AGENTS), 'Company': list(AI_AGENTS.values())}), hide_index=True)


# ── Data tab (notebook section 5) ────────────────────────────────────────────

def render_data(view, f):
    if view.empty:
        return nothing_here()
    col1, col2 = st.columns((2, 1))
    query = col1.text_input("URL contains", placeholder="e.g. /course or chatgpt", key="data_query")
    present = [label for label in STATUS_LABELS if (view['status_cat'] == label).any()]
    picked = col2.multiselect("Status", present, placeholder="Any status", key="data_status")

    rows = view
    if query:
        rows = rows[rows['url'].str.contains(query, case=False, regex=False)]
    if picked:
        rows = rows[rows['status_cat'].isin(picked)]
    time_col = 'local_time' if f.server_clock else 'timestamp'
    shown = rows.sort_values('timestamp', ascending=False)[
        [time_col, 'ip', 'method', 'url', 'status', 'size', 'referer', 'user_agent', 'section', 'is_static',
         'is_bot', 'browser', 'device', 'country', 'city']]

    st.caption(f"{len(rows):,} of {len(view):,} {f.noun}, newest first.")
    st.dataframe(shown, hide_index=True, placeholder="—", column_config={
        time_col: st.column_config.DatetimeColumn(f"Time ({f.clock_label})", format="YYYY-MM-DD HH:mm:ss"),
        'size': st.column_config.NumberColumn("Bytes", format="localized"),
        'status': st.column_config.NumberColumn(format="%d"),
        'is_static': "Static", 'is_bot': "Bot"})
    st.download_button("Download these rows (CSV)", data=lambda: shown.to_csv(index=False),
                       file_name="weblog_rows.csv", mime="text/csv", icon=":material/download:", on_click="ignore")

    with st.expander("Schema: what each column holds"):
        schema = pd.DataFrame({'dtype': view.dtypes.astype(str), 'non_null': view.count(),
                               'description': pd.Series(COLUMN_NOTES)}).rename_axis('column').reset_index()
        st.dataframe(schema, hide_index=True, column_config={
            'non_null': st.column_config.NumberColumn("Non-null", format="localized")})
    with st.expander("Numeric summary"):
        st.dataframe(view[['status', 'size', 'hour', 'day_of_week']].describe().round(1))
    with st.expander("How a log line becomes a row"):
        st.markdown("""
1. **Parse.** A regular expression splits each line into IP, timestamp, method, URL, status, size, referrer and
   user agent. Lines it can't read, such as empty requests, are skipped.
2. **Time.** The timestamp text becomes a UTC datetime, and from it the date, hour, day of week and month.
3. **Static files.** URLs ending in `.css`, `.js`, `.png` … or under `/css/`, `/js/`, `/images/`, `/socket.io/` …
   are marked `is_static`.
4. **Bots.** User agents containing *bot*, *crawler*, *spider*, *Googlebot*, *bingbot* … are marked `is_bot`.
5. **Buckets.** Status codes fall into `status_cat` (200 → 2xx Success, 404 → 4xx Client Err), and the first
   path segment becomes `section` (/course/cis511/syllabus → /course).
6. **Extras for this dashboard.** Browser, OS and device from the user agent; country and city from
   GeoLite2-City.mmdb; the course code in the URL; ChatGPT-page traffic; known AI crawlers; and scans for
   software the site doesn't run.
""")
