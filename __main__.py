from bitdeli import Profiles, Title, Description, set_theme
from bitdeli.textutil import Percent, country_name

from datetime import datetime
from collections import Counter
from itertools import chain

TOP_N=5
TREND_WINDOW=7 #days
TREND_NOISE_LIMIT=25 #users
text = {'window': TREND_WINDOW,
        'trend_change': Percent(0)}

set_theme('builder')

def day(hour):
    return datetime.utcfromtimestamp(hour * 3600).toordinal()

def daily_stats(profiles):
    all_stats = {}
    num_profiles_all = num_profiles_country = 0
    for profile in profiles:
        num_profiles_all += 1
        pcountries = profile['properties'].get('mp_country_code')
        if pcountries:
            num_profiles_country += 1
            for ccode, hours in pcountries.iteritems():
                country_stats = all_stats.get(ccode)
                if not country_stats:
                    all_stats[ccode] = country_stats = Counter()
                country_stats.update(frozenset(day(hour) for hour, freq in hours))
    return num_profiles_country / float(num_profiles_all), all_stats

def global_stats(stats):
    summarized = dict((ccode, sum(days.itervalues()))
                      for ccode, days in stats.iteritems())
    top = [{'Country': country_name(ccode), 'Users': users}
           for ccode, users in sorted(summarized.iteritems(),
                                        key=lambda x: x[1],
                                        reverse=True)][:TOP_N]
    for i, item in enumerate(top[:3]):
        text['top%d' % i] = item['Country']

    yield {'type': 'map',
           'label': 'User Distribution',
           'size': (6, 3),
           'data': summarized}
    yield {'type': 'table',
           'label': 'Top Countries',
           'size': (4, 3),
           'data': top}

def trending(stats):
    def scores():
        now = max(max(days) for days in stats.itervalues())
        for ccode, days in stats.iteritems():
            cutoff = now - TREND_WINDOW
            current = sum(days[day] for day in range(cutoff, now + 1))
            past = sum(days[day] for day in range(now - (TREND_WINDOW * 2 + 1),
                                                  cutoff))
            if current > TREND_NOISE_LIMIT or past > TREND_NOISE_LIMIT:
                yield float(current - past) / max(1, past),\
                      current,\
                      ccode

    def table(scored):
        for ratio, count, ccode in scored:
            arrow = '&darr;' if ratio < 0 else '&uarr;'
            yield {'Country': country_name(ccode),
                   'Change': '%s %d%%' % (arrow, ratio * 100),
                   'Users (past %d days)' % TREND_WINDOW: count}

    scored = list(sorted(scores(),
                         key=lambda x: abs(x[0]),
                         reverse=True))[:TOP_N]

    if scored:
        text['trending'] = country_name(scored[0][2])
        text['trend_change'] = Percent(scored[0][0])

    yield {'type': 'map',
           'label': 'Trending Countries',
           'size': (6, 3),
           'color': 2,
           'data': dict((ccode, abs(ratio))
                         for ratio, count, ccode in scored)}

    yield {'type': 'table',
           'label': 'Trending Countries',
           'size': (4, 3),
           'data': list(table(scored))}

def country_stats(profiles):
    text['cover'], stats = daily_stats(profiles)
    if stats:
        return chain(global_stats(stats), trending(stats))
    else:  
        return []

Profiles().map(country_stats).show()

Title("""
Top Geo Trend: Usage in {trending} has {trend_change.verb} by {trend_change}
""", text)

Description("""
The top three most active countries are now {top0}, {top1} and {top2}.
Trending is based on the user activity during the past {window} days.
Geographic information is available for {cover:.1%} of all user profiles.
""", text)

