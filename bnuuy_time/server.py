from datetime import datetime
import random
import statistics
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from flask import Flask, redirect
import pyhtml as p

from bnuuy_time.util import red_scale

from .buns import (
    DEFAULT_FOCUS,
    BunDefinition,
    bun_statistics,
    find_bun_with_filename,
    find_matching_bun,
    find_matching_buns,
    generate_time_for_bun,
)

from .times import format_time, now_in_tz, parse_time


app = Flask(__name__)


platform_logos = {
    "instagram": "/static/instagram.png",
    "reddit": "/static/reddit.png",
}


def platform_logo(platform: str):
    platform = platform.lower()
    print(platform)
    if platform in platform_logos:
        return p.img(src=platform_logos[platform.lower()], class_="platform-logo")
    else:
        return p.span()


def generate_head(
    title: str | None,
    extra_css: list[str],
):
    title = f"{title} - Bnuuy Time" if title else "Bnuuy time"
    return p.head(
        p.title(title),
        p.link(rel="stylesheet", href="/static/root.css"),
        [p.link(rel="stylesheet", href=css_file) for css_file in extra_css],
        p.meta(
            name="description",
            content="When you visit this webpage, a bunny rabbit will tell you what time it is",
        ),
        p.meta(name="keywords", content="clock, time, bunny, rabbit, Maddy Guthridge"),
        p.meta(name="author", content="Maddy Guthridge"),
        p.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        # Refresh every minute
        p.meta(http_equiv="refresh", content="60"),
    )


def top_links():
    return p.header(class_="shadow")(
        p.span("Bnuuy Time"),
        p.span(class_="hide-mobile")("•"),
        p.span(class_="hide-mobile")(
            p.a(href="https://maddyguthridge.com")("Made with <3 by Maddy Guthridge")
        ),
        p.span("•"),
        p.span(p.a(href="/about")("About")),
    )


def bnuuy_time(bun: BunDefinition, time: datetime):
    t = format_time(time)

    name = bun["name"]
    if name is None:
        name = random.choice(["Bun", "Bunny", "Bnuuy"])
    elif isinstance(name, list):
        name = random.choice(name)

    # Credits
    source = bun["source"]
    if source is not None:
        credits = p.a(href=source["url"], target="_blank")(
            platform_logo(source["platform"]),
            f"{source['author']}",
        )
    else:
        credits = None

    # Focus point
    focus_x = bun.get("focus_x", DEFAULT_FOCUS)
    focus_y = bun.get("focus_y", DEFAULT_FOCUS)

    time_adjective = random.choice(
        [
            "says that it is",
            "says the time is",
            "says it's",
            "says that it's",
            "says it is",
        ]
    )

    return str(
        p.html(
            generate_head(t, ["/static/buns.css"]),
            p.body(
                p.div(class_="background-container")(
                    p.img(
                        id="bun-img",
                        style=f"--crop-focus-x: {focus_x}; --crop-focus-y: {focus_y}",
                        src=f"/static/buns/{bun['filename']}",
                        alt=f"{name}'s ears are telling the time like an analog clock, and say that the time is {t}",
                    ),
                ),
                top_links(),
                p.div(class_="center")(
                    p.main(
                        p.h1(class_="shadow")(
                            f"{name} {time_adjective}",
                            p.span(class_="no-wrap")(t),
                        ),
                        p.span(class_="shadow")("Credit: ", credits) if credits else [],
                    ),
                ),
            ),
        )
    )


def error_page(reason: str):
    return str(
        p.html(
            generate_head("Error", []),
            p.body(
                p.h1("No matching bunnies"),
                p.p(reason),
                p.p("I'll add more bunnies over time..."),
            ),
        )
    )


@app.get("/")
def redirect_with_tz():
    return str(
        p.html(
            generate_head(None, []),
            p.body(
                p.h1("Bnuuy time"),
                p.p("Redirecting to your time zone..."),
                p.script(src="/static/tz_redirect.js"),
            ),
        )
    )


@app.get("/about")
def about_page():
    statistics = bun_statistics()
    return str(
        p.html(
            generate_head("About", ["/static/about.css"]),
            p.body(
                p.main(
                    p.h1("About -", p.a(href="/")("Bnuuy Time")),
                    p.article(
                        p.p(
                            "This website is a collection of rabbit photos, where "
                            "each bunny's ears form an analog clock showing the "
                            "current time. Currently, the site contains "
                            f"{statistics['num_buns']} bunnies."
                        ),
                        p.p(
                            "Project made with <3 by ",
                            p.a(href="https://maddyguthridge.com")("Maddy Guthridge"),
                            ".",
                        ),
                        p.h2("A bunny's ears are wrong! Why?"),
                        p.p(
                            "The website picks bunnies by comparing the angle of "
                            "their ears to the angle of the hands on an analog clock. "
                            "Sometimes, it can't find a bunny whose ears are close "
                            "enough, and so it picks the closest it can find. "
                            "You can determine times with the best (and "
                            "worst) bunny coverage ",
                            p.a(href="/coverage")("here"),
                            ".",
                        ),
                        p.h2("Can I add my own bunny's photos to the site?"),
                        p.p(
                            "I'd love to include your bunnies on the site! Currently "
                            "I'll need to add them myself, so feel free to reach out "
                            "and send some bun photos to me! Currently, the site "
                            "doesn't have a system for uploading photos yourself, but "
                            "if you're interested in this, shoot me a message."
                        ),
                        p.h2("How are you making money?"),
                        p.p(
                            "I'm not. I made this project for fun, and have no "
                            "intention of monetizing it. However, if you want to "
                            "support my work, I'd love if you ",
                            p.a(href="https://buymeacoffee.com/maddyguthridge")(
                                "buy me a bowl of pasta"
                            ),
                            ". No pressure, of course!",
                        ),
                        p.h2("Are you tracking and selling my data?"),
                        p.p(
                            "I use Cloudflare analytics to keep track of "
                            "visitors to my site. This data is not sold by me "
                            "or by Cloudflare, and is used exclusively for "
                            "gathering insights into site and page popularity."
                        ),
                    ),
                ),
            ),
        )
    )


@app.get("/coverage")
def coverage():
    coverage_times = []
    degree_discrepancies: list[int] = []
    for hour in range(1, 13):
        for minute in range(0, 60, 5):
            t = datetime.now().replace(hour=hour, minute=minute)
            buns = find_matching_buns(t)
            num_buns = len(buns)
            closest_bun = min(bun[0] for bun in buns)
            degree_discrepancies.append(closest_bun)

            # 3 buns is great coverage
            bg_num_buns = red_scale(num_buns / 3)
            # 30 degrees away is bad
            bg_closest_buns = red_scale((30 - closest_bun) / 10)

            # Make each hour have a background colour for readability
            time_bgs = {
                # Blue
                0: "rgb(200, 200, 255)",
                # Red
                15: "rgb(255, 200, 200)",
                # Green
                30: "rgb(200, 255, 200)",
                # Red
                45: "rgb(255, 200, 200)",
            }
            bg_time = time_bgs.get(minute, "rgb(255, 255, 255)")

            coverage_times.append(
                p.tr(
                    p.td(style=f"background-color: {bg_time}")(f"{hour}:{minute:02}"),
                    p.td(style=f"background-color: {bg_num_buns}")(f"{num_buns}"),
                    p.td(style=f"background-color: {bg_closest_buns}")(
                        f"{closest_bun}"
                    ),
                )
            )

    average_discrepancy = statistics.mean(degree_discrepancies)

    return str(
        p.html(
            generate_head(
                "Bun coverage", ["/static/coverage.css", "/static/about.css"]
            ),
            p.body(
                p.main(
                    p.h1("Coverage -", p.a(href="/")("Bnuuy Time")),
                    p.p(f"Mean angle discrepancy: {average_discrepancy:.0f}deg"),
                    p.table(
                        p.thead(
                            p.tr(
                                p.th("Time"),
                                p.th("Matching buns"),
                                p.th("Angle difference"),
                            ),
                        ),
                        p.tbody(
                            coverage_times,
                        ),
                    ),
                )
            ),
        )
    )


@app.get("/buns/<path:bun_file>")
def with_bun(bun_file: str):
    bun = find_bun_with_filename(bun_file)

    if bun is None:
        return error_page(f"No buns with filename {bun_file}")
    else:
        return bnuuy_time(bun, generate_time_for_bun(bun))


@app.get("/<time_str>")
def at_time(time_str: str):
    # Convenience redirects for common time zones
    abbreviation_redirects = {
        "UTC": "Etc/UTC",
        "GMT": "Europe/London",
    }
    if time_str in abbreviation_redirects:
        return redirect(f"{abbreviation_redirects[time_str]}")

    parsed = parse_time(time_str)

    if parsed is None:
        return error_page(f"Unable to parse the time string '{time_str}'")
    else:
        bun = find_matching_bun(parsed)
        if bun is None:
            return str(error_page(f"No matching buns at {format_time(parsed)} :("))
        return bnuuy_time(bun, parsed)


@app.get("/<region>/<location>")
def from_region(region: str, location: str):
    try:
        now = now_in_tz(ZoneInfo(f"{region}/{location}"))
    except ZoneInfoNotFoundError:
        return error_page(f"The time zone '{region}/{location}' does not exist")
    bun = find_matching_bun(now)
    if bun is None:
        return error_page(f"No matching buns at {format_time(now)} :(")
    return bnuuy_time(bun, now)


if __name__ == "__main__":
    app.run()
