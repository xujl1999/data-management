from pathlib import Path
import json
import random
import time
from typing import Dict, List

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from tqdm import tqdm

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config() -> Dict:
    raw = CONFIG_PATH.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(raw)
    return json.loads(raw)


def random_between(span: List[float]) -> float:
    return random.uniform(span[0], span[1])


def human_scroll(driver: webdriver.Edge, min_scrolls: int, max_scrolls: int) -> None:
    steps = random.randint(min_scrolls, max_scrolls)
    for _ in range(steps):
        scroll_px = random.randint(300, 1200)
        driver.execute_script(
            "window.scrollBy({ top: arguments[0], behavior: 'smooth' });", scroll_px
        )
        time.sleep(random_between([0.8, 1.6]))
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(random_between([0.5, 1.0]))


def build_driver(edge_options: List[str], headless: bool) -> webdriver.Edge:
    options = Options()
    for opt in edge_options:
        options.add_argument(opt)
    if headless:
        # 使用新版 headless 以减少兼容性问题
        options.add_argument("--headless=new")
    driver = webdriver.Edge(options=options)
    driver.get("https://www.bilibili.com")
    time.sleep(random_between([1.5, 3.5]))
    return driver


def load_authors(authors_path: Path) -> List[Dict]:
    with authors_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def collect_for_author(
    driver: webdriver.Edge,
    author: Dict,
    sleep_after_load: List[float],
    scroll_min: int,
    scroll_max: int,
    max_videos: int,
) -> List[Dict]:
    author_id = author["author_id"]
    category = author.get("category", "")

    driver.get(f"https://space.bilibili.com/{author_id}/upload/video")
    time.sleep(random_between(sleep_after_load))
    human_scroll(driver, scroll_min, scroll_max)

    collected: List[Dict] = []
    for rank in range(1, max_videos + 1):
        try:
            base = f"#app > main > div.space-upload > div.upload-content > div > div.video-body > div > div:nth-child({rank}) > div > div > div > div > div.bili-video-card"
            url = (
                driver.find_element(By.CSS_SELECTOR, f"{base}__cover > a")
                .get_attribute("href")
                .split("?", 1)[0]
            )
            title = driver.find_element(
                By.CSS_SELECTOR, f"{base}__details > div.bili-video-card__title > a"
            ).text
            publish_date = driver.find_element(
                By.CSS_SELECTOR, f"{base}__details > div.bili-video-card__subtitle > span"
            ).text
            author_name = driver.find_element(
                By.CSS_SELECTOR,
                "#app > div.header.space-header > div.upinfo.header-upinfo > div.upinfo__main > div.upinfo-detail > div.upinfo-detail__top > div.nickname",
            ).text
        except Exception:
            break

        collected.append(
            {
                "category": category,
                "author": author_name,
                "rank": rank,
                "publish_date": publish_date,
                "title": title,
                "url": url,
            }
        )
        print(f"{author_name} - {title}")
    return collected


def write_outputs(rows: List[Dict], outputs: List[str]) -> None:
    df = pd.DataFrame(rows)
    for out in outputs:
        target = (BASE_DIR / out).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(target, index=False)


def main() -> None:
    config = load_config()
    authors_path = BASE_DIR / config["authors_file"]
    authors = load_authors(authors_path)
    driver = build_driver(
        config.get("edge_options", []),
        headless=config.get("headless", False),
    )

    rows: List[Dict] = []
    try:
        for author in tqdm(authors):
            rows.extend(
                collect_for_author(
                    driver,
                    author,
                    sleep_after_load=config["sleep_after_load_seconds"],
                    scroll_min=config["scroll_steps"]["min"],
                    scroll_max=config["scroll_steps"]["max"],
                    max_videos=config["max_videos_per_author"],
                )
            )
    finally:
        driver.quit()

    write_outputs(rows, config["outputs"])


if __name__ == "__main__":
    main()
