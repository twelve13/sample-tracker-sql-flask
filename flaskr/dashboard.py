from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
# list all the samples
def index():
    db = get_db()
    samples = db.execute(
        'SELECT id, sampleName, analyst, notes, strs, mito, isPriority, cleaned, sampled, extraction_name'
        ' FROM sample'
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
            "SELECT id, sampleName, analyst, notes, strs, mito, isPriority, cleaned, sampled"
            " FROM sample"
            " WHERE id = ?",
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
    # Create a new sample.
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
    # Update a sample
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


@bp.route("/<int:id>/assignSample", methods=("GET", "POST"))
# assign a sample to an extraction set
@login_required
def assignSample(id):
    sample = get_sample(id)

    db = get_db()
    extractions = db.execute(
        'SELECT extractionName, id FROM extraction ORDER BY extractionName'
    ).fetchall()

    if request.method == "POST":
        # this will return the id 1, 2, 3 etc
        selectedExtraction = request.form.get("assigned-extraction")

        # select all items with this selectedExtraction id number
        selectedExtractionDb = db.execute(
            'SELECT extractionName FROM extraction WHERE id= ?', (selectedExtraction)
        ).fetchall()

        # then get the first row and its extractionName
        selectedExtractionName = selectedExtractionDb[0]['extractionName']

        error = None

        if error is not None:
            flash(error)
        else:
            db.execute(
                "UPDATE sample SET extraction_id = ?, extraction_name = ? WHERE id = ?", (selectedExtraction, selectedExtractionName, id)
            )
            db.commit()
            return redirect(url_for("dashboard.index"))

    return render_template("dashboard/assignSample.html", sample=sample, extractions=extractions)

@bp.route("/<int:id>/deleteSample", methods=("POST",))
@login_required
def deleteSample(id):
    # Delete a sample.
    get_sample(id)
    db = get_db()
    db.execute("DELETE FROM sample WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("dashboard.index"))




@bp.route("/extractions")
@login_required
def extractionsIndex():
    db = get_db()
    extractions = db.execute(
        'SELECT p.id, extractionName, goalDate, analyst, notes, bbpAdded, extracted'
        ' FROM extraction p'
        ' ORDER BY extractionName'
    ).fetchall()

    return render_template('dashboard/extractions.html', extractions=extractions)

def get_extraction(id, check_author=True):
    """Get an extraction and its author by id.
    :param id: id of sample to get
    :return: the sample with all associated info
    :raise 404: if a sample with the given id doesn't exist
    """
    extraction = (
        get_db()
        .execute(
            "SELECT p.id, extractionName, goalDate, analyst, notes, bbpAdded, extracted"
            " FROM extraction p"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if extraction is None:
        abort(404, "Extraction id {0} doesn't exist.".format(id))

    return extraction


@bp.route("/<int:id>/showExtractionSet", methods=("GET", "POST"))
def showExtractionSet(id):
    # Show associated samples
    extraction = get_extraction(id)

    db = get_db()
    associatedSamples = db.execute(
        'SELECT sampleName FROM sample WHERE extraction_id = ?', (id,),
    ).fetchall()

    return render_template('dashboard/showExtractionSet.html', extraction=extraction, associatedSamples=associatedSamples)

@bp.route("/createExtraction", methods=("GET", "POST"))
@login_required
def createExtraction():
    if request.method == "POST":
        extractionName = request.form["extraction-name"]
        goalDate = request.form["goal-date"]
        analyst = request.form["analyst"]
        notes = request.form["notes"]
        bbpAdded = 0
        extracted = 0
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
            return redirect(url_for("dashboard.extractionsIndex"))

    return render_template("dashboard/createExtraction.html")


@bp.route("/<int:id>/updateExtraction", methods=("GET", "POST"))
@login_required
def updateExtraction(id):
    # Update an extraction
    extraction = get_extraction(id)

    if request.method == "POST":
        extractionName = request.form["extraction-name"]
        goalDate = request.form["goal-date"]
        analyst = request.form["analyst"]
        notes = request.form["notes"]

        error = None

        if not extractionName:
            error = "Extraction name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE extraction SET extractionName = ?, goalDate = ?, analyst = ?, notes = ? WHERE id = ?", (extractionName, goalDate, analyst, notes, id)
            )
            db.commit()
            return redirect(url_for("dashboard.extractionsIndex"))

    return render_template("dashboard/updateExtraction.html", extraction=extraction)


@bp.route("/<int:id>/processExtraction", methods=("GET", "POST"))
# update if extraction set has had buffers added or has been extracted
@login_required
def processExtraction(id):
    extraction = get_extraction(id)

    if request.method == "POST":
        if request.form.get("bbpAdded"):
            bbpAdded = 1
        else:
            bbpAdded = 0
        if request.form.get("extracted"):
            extracted = 1
        else:
            extracted = 0
        error = None

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE extraction SET bbpAdded = ?, extracted = ? WHERE id = ?", (bbpAdded, extracted, id)
            )
            db.commit()
            return redirect(url_for("dashboard.extractionsIndex"))

    return render_template("dashboard/processExtraction.html", extraction=extraction)


@bp.route("/<int:id>/deleteExtraction", methods=("POST",))
@login_required
def deleteExtraction(id):
    # Delete an extraction.
    get_extraction(id)
    db = get_db()
    db.execute("DELETE FROM extraction WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("dashboard.extractionsIndex"))