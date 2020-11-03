from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('dashboard', __name__)

@bp.route('/')
# list all the samples
def index():
    db = get_db()
    samples = db.execute(
        'SELECT p.id, sampleName, analyst, notes, strs, mito, isPriority, cleaned, sampled'
        ' FROM sample p'
        ' ORDER BY sampleName'
    ).fetchall()
    return render_template('dashboard/index.html', samples=samples)


def get_sample(id, check_author=True):
    """Get a sample and its author by id.
    :param id: id of sample to get
    :return: the sample with all associated info
    :raise 404: if a sample with the given id doesn't exist
    """
    sample = (
        get_db()
        .execute(
            "SELECT p.id, sampleName, analyst, notes, strs, mito, isPriority, cleaned, sampled"
            " FROM sample p"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if sample is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    return sample


@bp.route("/createSample", methods=("GET", "POST"))
# create a new sample pulling from the createSample.html form
# since there is no boolean type for sql, convert checkboxes to 1 for checked, 0 for unchecked
# at creation, sample won't be cleaned or sampled, so just set to 0
@login_required
def createSample():
    """Create a new sample."""
    if request.method == "POST":
        sampleName = request.form["sample-name"]
        analyst = request.form["analyst"]
        notes = request.form["notes"]
        if request.form.get("strs"):
            strs = 1
        else:
            strs = 0
        if request.form.get("mito"):
            mito = 1
        else:
            mito = 0
        if request.form.get("is-priority"):
            isPriority = 1
        else:
            isPriority = 0

        cleaned = 0
        sampled = 0
        error = None

        if not sampleName:
            error = "Sample name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO sample (sampleName, analyst, notes, strs, mito, isPriority, cleaned, sampled) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (sampleName, analyst, notes, strs, mito, isPriority, cleaned, sampled),
            )
            db.commit()
            return redirect(url_for("dashboard.index"))

    return render_template("dashboard/createSample.html")


@bp.route("/<int:id>/updateSample", methods=("GET", "POST"))
@login_required
def updateSample(id):
    """Update a sample"""
    sample = get_sample(id)

    if request.method == "POST":
        sampleName = request.form["sample-name"]
        analyst = request.form["analyst"]
        notes = request.form["notes"]
        if request.form.get("strs"):
            strs = 1
        else:
            strs = 0
        if request.form.get("mito"):
            mito = 1
        else:
            mito = 0
        if request.form.get("is-priority"):
            isPriority = 1
        else:
            isPriority = 0
        error = None

        if not sampleName:
            error = "Sample name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE sample SET sampleName = ?, analyst = ?, notes = ?, strs = ?, mito = ?, isPriority = ? WHERE id = ?", (sampleName, analyst, notes, strs, mito, isPriority, id)
            )
            db.commit()
            return redirect(url_for("dashboard.index"))

    return render_template("dashboard/updateSample.html", sample=sample)

@bp.route("/<int:id>/processSample", methods=("GET", "POST"))
# update if sample is cleaned or sampled
@login_required
def processSample(id):
    sample = get_sample(id)

    if request.method == "POST":
        if request.form.get("cleaned"):
            cleaned = 1
        else:
            cleaned = 0
        if request.form.get("sampled"):
            sampled = 1
        else:
            sampled = 0
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE sample SET cleaned = ?, sampled = ? WHERE id = ?", (cleaned, sampled, id)
            )
            db.commit()
            return redirect(url_for("dashboard.index"))

    return render_template("dashboard/processSample.html", sample=sample)

@bp.route("/<int:id>/deleteSample", methods=("POST",))
@login_required
def deleteSample(id):
    """Delete a sample.
    """
    get_sample(id)
    db = get_db()
    db.execute("DELETE FROM sample WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("dashboard.index"))

@bp.route("/extractions")
def extractionsIndex():
    db = get_db()
    extractions = db.execute(
        'SELECT p.id, extractionName, goalDate, analyst, notes, bbpAdded, extracted'
        ' FROM extraction p'
        ' ORDER BY extractionName'
    ).fetchall()
    return render_template('dashboard/extractions.html', extractions=extractions)



@bp.route("/createExtraction", methods=("GET", "POST"))
@login_required
def createExtraction():
    """Create a new post for the current user."""
    if request.method == "POST":
        extractionName = request.form["extraction-name"]
        goalDate = request.form["goal-date"]
        analyst = request.form["analyst"]
        notes = request.form["notes"]
        bbpAdded = request.form["bbp-added"]
        extracted = request.form["extracted"]
        error = None

        if not extractionName:
            error = "Extraction name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO extraction (extractionName, goalDate, analyst, notes, bbpAdded, extracted) VALUES (?, ?, ?, ?, ?, ?)",
                (extractionName, goalDate, analyst, notes, bbpAdded, extracted),
            )
            db.commit()
            return redirect(url_for("dashboard.extractions"))

    return render_template("dashboard/createExtraction.html")

@bp.route("/<int:id>/updateExtraction", methods=("GET", "POST"))
@login_required
def updateExtraction(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/updateExtraction.html", post=post)