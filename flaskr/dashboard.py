from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
# List all the samples
def index():
    db = get_db()
    samples = db.execute(
        'SELECT id, sampleName, analyst, notes, strs, mito, isPriority, cleaned, sampled, extraction_name'
        ' FROM sample'
        ' ORDER BY sampleName'
    ).fetchall()

    extractions = db.execute(
        'SELECT extractionName, id FROM extraction ORDER BY extractionName'
    ).fetchall()
    
    return render_template('dashboard/index.html', samples=samples, extractions=extractions)

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
# Create a new sample pulling from the createSample.html form
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
# Update a sample using form
def updateSample(id):
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


@bp.route("/<int:id>/markSampleCleaned", methods=("POST",))
@login_required
# Update sample to true for "cleaned" field
def markSampleCleaned(id):
    get_sample(id)
    db = get_db()
    db.execute(
        "UPDATE sample SET cleaned = ? WHERE id = ?", (1, id)
    )
    db.commit()
    return redirect(url_for("dashboard.index"))


@bp.route("/<int:id>/markSampleSampled", methods=("POST",))
@login_required
# Update sample to true for "sampled" field
def markSampleSampled(id):
    get_sample(id)
    db = get_db()
    db.execute(
        "UPDATE sample SET sampled = ? WHERE id = ?", (1, id)
    )
    db.commit()
    return redirect(url_for("dashboard.index"))


@bp.route("/<int:id>/assignSample", methods=("GET", "POST"))
@login_required
# Assign a sample to an extraction set
def assignSample(id):
    sample = get_sample(id)
    db = get_db()

    if request.method == "POST":
        # this will return the id 1, 2, 3 etc
        selectedExtraction = request.form.get("assigned-extraction")

        # select all items with this selectedExtraction id number
        selectedExtractionDb = db.execute(
            'SELECT extractionName FROM extraction WHERE id= ?', (selectedExtraction,)
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

    
@bp.route("/<int:id>/deleteSample", methods=("POST",))
@login_required
# Delete a sample from database
def deleteSample(id):
    get_sample(id)
    db = get_db()
    db.execute("DELETE FROM sample WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("dashboard.index"))


@bp.route("/extractions")
@login_required
# List all the Extraction sets
def extractionsIndex():
    # The only way I could figure out how to tack on each extraction's associated samples was to create another array called extractionsWithSamples, and for each extraction, tack on all the extraction info along with its associated samples that we get from another query
    extractionsWithSamples = []
    db = get_db()
    extractions = db.execute(
        'SELECT p.id, extractionName, goalDate, analyst, notes, bbpAdded, extracted'
        ' FROM extraction p'
        ' ORDER BY extractionName'
    ).fetchall()

    for extraction in extractions:
   
        extractionId = extraction['id']

        db = get_db()
        associatedSamples = db.execute(
            'SELECT sampleName FROM sample WHERE extraction_id = ?', (extractionId,),
        ).fetchall()

        extractionsWithSamples.append(
            {"id": extraction['id'],
            "extractionName": extraction['extractionName'], 
            "goalDate": extraction['goalDate'], 
            "analyst": extraction['analyst'], 
            "notes": extraction['notes'],
            "bbpAdded": extraction['bbpAdded'],
            "extracted": extraction['extracted'],
            "associatedSamples": associatedSamples
            }
        )

    return render_template('dashboard/extractions.html', extractions=extractions, extractionsWithSamples=extractionsWithSamples)

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


@bp.route("/createExtraction", methods=("GET", "POST"))
@login_required
# Create an extraction using form
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
# Update an extraction using form
def updateExtraction(id):
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


@bp.route("/<int:id>/markExtractionBuffersAdded", methods=("POST",))
@login_required
# Update extraction to true for "bbpAdded" field
def markExtractionBuffersAdded(id):
    get_extraction(id)
    db = get_db()
    db.execute(
        "UPDATE extraction SET bbpAdded = ? WHERE id = ?", (1, id)
    )
    db.commit()
    return redirect(url_for("dashboard.extractionsIndex"))


@bp.route("/<int:id>/markExtractionExtracted", methods=("POST",))
@login_required
# Update extraction to true for "extracted" field
def markExtractionExtracted(id):
    get_extraction(id)
    db = get_db()
    db.execute(
        "UPDATE extraction SET extracted = ? WHERE id = ?", (1, id)
    )
    db.commit()
    return redirect(url_for("dashboard.extractionsIndex"))


@bp.route("/<int:id>/deleteExtraction", methods=("POST",))
@login_required
# Delete an extraction from the database
def deleteExtraction(id):
    get_extraction(id)
    db = get_db()
    db.execute("DELETE FROM extraction WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("dashboard.extractionsIndex"))


@bp.route("/<int:id>/archiveExtraction", methods=("GET", "POST"))
#Add samples to archive table, remove samples from samples table, remove extraction from extractions table
def archiveExtraction(id):
    extraction = get_extraction(id)

    db = get_db()
    associatedSamples = db.execute(
        'SELECT * FROM sample WHERE extraction_id = ?', (id,),
    ).fetchall()

    for sample in associatedSamples:

        db.execute(
            "INSERT INTO archive (sampleName, analyst, notes, strs, mito, extraction_name) VALUES (?, ?, ?, ?, ?, ?)",
            (sample["sampleName"], sample["analyst"], sample["notes"], sample["strs"], sample["mito"], sample["extraction_name"]),
        )

        sampleId = sample["id"]

        db.execute("DELETE FROM sample WHERE id = ?", (sampleId,))
        db.execute("DELETE FROM extraction WHERE id = ?", (id,))

        db.commit()

    return redirect(url_for("dashboard.extractionsIndex"))


@bp.route('/archive')
@login_required
# List all the archived samples
def showArchive():
    db = get_db()
    samples = db.execute(
        'SELECT id, sampleName, analyst, notes, strs, mito, extraction_name'
        ' FROM archive'
        ' ORDER BY sampleName'
    ).fetchall()
    
    return render_template('dashboard/archive.html', samples=samples)