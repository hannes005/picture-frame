import sqlite3
from pathlib import Path
from uuid import uuid4
from PIL import Image, ImageOps
import os

DB_PATH = "./datastore/datastore.db"

#Path for storing uploaded originals
IMAGE_UPLOAD_DIR = Path("./datastore/media/original")
IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

#Path for storing thumbnails
IMAGE_THUMBNAIL_DIR = Path("./datastore/media/thumbnail")
IMAGE_THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

#Path for storing to-be-displayed versions images.
IMAGE_OPTIMIZED_DIR = Path("./datastore/media/optimized")
IMAGE_OPTIMIZED_DIR.mkdir(parents=True, exist_ok=True)

def get_db_conn() -> sqlite3.Connection:
    """Create configured SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():

    print("DB initialization")
    print("DB Path" + DB_PATH)

    with get_db_conn() as conn:
        cur = conn.cursor()

        # Create photos table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY,
            path_original TEXT NOT NULL,
            path_thumbnail TEXT NOT NULL,
            path_optimized TEXT NOT NULL,
            processed INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events(id)
        )
        """)

        # Create events table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL
        )
        """)

def add_event(title):

    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO events (
                title
            )
            VALUES (?)
        """, (
            title,
        ))

        conn.commit()

def rename_event(event_id, new_title):

    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            UPDATE events
            SET title = ?
            WHERE id = ?
        """, (
            new_title,
            event_id,
        ))

        conn.commit()


def get_events_bak():

    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                title
            FROM events
        """)

        events = cur.fetchall()

    return events

def get_events():

    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                events.id,
                events.title,
                COUNT(photos.id) AS image_count
            FROM events
            LEFT JOIN photos
                ON photos.event_id = events.id
            GROUP BY events.id, events.title
            ORDER BY events.id DESC
        """)

        return cur.fetchall()

def get_event(event_id):

    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                title
            FROM events
            WHERE id = ?
        """, (event_id,))

        event = cur.fetchone()

    return event


def get_images_for_event(event_id):

    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT
                id,
                path_thumbnail,
                path_optimized
            FROM photos
            WHERE event_id = ?
            ORDER BY id
        """, (event_id,))

    return cur.fetchall()

def get_image(image_id):
    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT id,
                path_original,
                path_thumbnail,
                path_optimized,
                processed,
                event_id
            FROM photos
            WHERE id = ?
            """, (image_id,))

        image = cur.fetchone()

    return image


def delete_image(image_id):

    #Load complete image data from database
    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT event_id,
                path_original,
                path_thumbnail,
                path_optimized
            FROM photos
            WHERE id = ?
            """, (image_id,)
        )

        image = cur.fetchone()

    if image is None:
        return None
    event_id = image["event_id"]
   
    # Delete the physical files
    for path in (image["path_original"],image["path_thumbnail"],image["path_optimized"]):
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
            
    # Delete database record
    with get_db_conn() as conn:
        cur = conn.cursor()

        conn.execute(
            "DELETE FROM photos WHERE id = ?",
            (image_id,)
        )

        conn.commit()


def delete_event(event_id):

    #Get all images for this event
    images = get_images_for_event(event_id)

    #Delete all contained images
    for image in images:
        image_id = image["id"]
        delete_image(image_id)

    # Delete database record for event
    with get_db_conn() as conn:
        cur = conn.cursor()

        conn.execute(
            "DELETE FROM events WHERE id = ?",
            (event_id,)
        )

        conn.commit()
    
    

def add_image(image, event_id):

    #Lower file extension
    extension = Path(image.filename).suffix.lower()

    #Create unique filename for each uploaded file.
    filename = f"{uuid4()}{extension}"
    destination = IMAGE_UPLOAD_DIR / filename

    #In case of filename already existing, create new filename:
    while destination.exists():
        filename = f"{uuid4()}{extension}"
        destination = UPLOAD_DIR / filename

    #Write file to filesystem
    with destination.open("wb") as f:
        while chunk := image.file.read(1024 * 1024):
            f.write(chunk)

    #Add database entry which represents this image
    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO photos (
                path_original,
                path_optimized,
                path_thumbnail,
                processed,
                event_id
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(destination),
            "",
            "",
            0,
            event_id
        ))

    conn.commit()

    #Trigger thumbnail generation
    image_id = cur.lastrowid  #Gets las low inserted by this cursor!
    generate_thumbnail(image_id)

    #Trigger optimized generation
    image_id = cur.lastrowid  #Gets las low inserted by this cursor!
    generate_optimized(image_id)


def generate_thumbnail(image_id):

    #Load original file path from database
    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT path_original
            FROM photos
            WHERE id = ?
        """, (image_id,))

        image = cur.fetchone()

        if image is None:
            return False

        original_path = Path(image[0])

    #Generate thumbnail path
    thumbnail_filename = original_path.stem + ".jpg"
    thumbnail_path = IMAGE_THUMBNAIL_DIR / thumbnail_filename

    #Generate thumbnail file
    with Image.open(original_path) as image:
        image = ImageOps.exif_transpose(image) #Applys rotation information from exif data
        image.thumbnail((400, 400))
        image.convert("RGB").save(thumbnail_path, "JPEG", quality=75)

    #Save thumbnail path to database
    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            UPDATE photos
            SET path_thumbnail = ?
            WHERE id = ?
        """, (
            str(thumbnail_path),
            image_id)
        )

        conn.commit()

    return True


def generate_optimized(image_id):

    #Load original file path from database
    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT path_original
            FROM photos
            WHERE id = ?
        """, (image_id,))

        image = cur.fetchone()

        if image is None:
            return False

        original_path = Path(image[0])

    #Generate path for image version "optimized"
    optimized_filename = original_path.stem + ".jpg"
    optimized_path = IMAGE_OPTIMIZED_DIR / optimized_filename

    #Generate optimized image file
    with Image.open(original_path) as image:
        image = ImageOps.exif_transpose(image) #Applys rotation information from exif data
        image.thumbnail((1920, 1080))
        image.convert("RGB").save(optimized_path, "JPEG", quality=92)

    #Save optimized path to database
    with get_db_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
            UPDATE photos
            SET path_optimized = ?
            WHERE id = ?
        """, (
            str(optimized_path),
            image_id)
        )

        conn.commit()

    return True