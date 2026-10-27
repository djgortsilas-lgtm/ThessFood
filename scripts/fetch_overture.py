"""Κατεβάζει τα Overture Maps Places για το bbox της Θεσσαλονίκης -> data/raw/overture.json
Χρήση: python scripts/fetch_overture.py [--schema]
Τραβάει ΟΛΑ τα places του bbox (το φιλτράρισμα εστίασης γίνεται στο build_data.py).
"""
import json, sys, pathlib, urllib.request
import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ext" / "overture.json"
BBOX = dict(xmin=22.75, xmax=23.15, ymin=40.50, ymax=40.75)  # ίδιο με το Overpass query

def latest_release():
    req = urllib.request.Request("https://stac.overturemaps.org/catalog.json",
                                 headers={"User-Agent": "Mozilla/5.0 thess-food"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["latest"]

def main():
    rel = latest_release()
    print("Overture release:", rel)
    src = f"s3://overturemaps-us-west-2/release/{rel}/theme=places/type=place/*.parquet"
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")
    if "--schema" in sys.argv:
        for row in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{src}', hive_partitioning=1)").fetchall():
            print(row[0], "|", row[1][:200])
        return
    q = f"""
      SELECT id, confidence, websites, emails, socials, phones,
             brand.names."primary" AS brand, names."primary" AS name, names.common AS names_common,
             addresses, operating_status, basic_category, taxonomy,
             list_transform(sources, lambda s: s.dataset) AS datasets,
             ST_X(geometry) AS lon, ST_Y(geometry) AS lat
      FROM read_parquet('{src}', hive_partitioning=1)
      WHERE bbox.xmin BETWEEN {BBOX['xmin']} AND {BBOX['xmax']}
        AND bbox.ymin BETWEEN {BBOX['ymin']} AND {BBOX['ymax']}
    """
    rel_ = con.execute(q)
    cols = [d[0] for d in rel_.description]
    rows = [dict(zip(cols, r)) for r in rel_.fetchall()]
    OUT.write_text(json.dumps({"release": rel, "places": rows}, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"{len(rows)} places -> {OUT} ({OUT.stat().st_size//1024} KB)")

if __name__ == "__main__":
    main()
