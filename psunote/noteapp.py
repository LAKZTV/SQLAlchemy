import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )

@app.route("/notes/remove/<int:note_id>", methods=["POST"])
def remove_note(note_id):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.id == note_id)).scalars().first()

    if note:
        db.session.delete(note)
        db.session.commit()

    return flask.redirect(flask.url_for("index"))

@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id):
    db = models.db

    # Retrieve the note by ID from the database
    note = db.session.execute(db.select(models.Note).where(models.Note.id == note_id)).scalars().first()

    if not note:
        flask.abort(404)  # Return a 404 error if the note is not found

    if flask.request.method == "POST":
        # Update note details from the form
        note.title = flask.request.form['title']
        note.description = flask.request.form['description']
        
        # Clear existing tags and add new ones
        note.tags.clear()
        tag_names = flask.request.form['tags'].split(',')
        for tag_name in tag_names:
            tag_name = tag_name.strip()  # Remove extra spaces
            if tag_name:  # Ensure tag name is not empty
                tag = (
                    db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
                    .scalars()
                    .first()
                )

                if not tag:
                    tag = models.Tag(name=tag_name)  # Create a new Tag if it doesn't exist
                    db.session.add(tag)

                note.tags.append(tag)  # Append the Tag object to the note's tags

        db.session.commit()  # Commit changes to the database
        return flask.redirect(flask.url_for("index"))  # Redirect to index after saving

    # Render the edit form with the note data
    return flask.render_template("edit-note.html", note_id=note.id, note=note)




@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


if __name__ == "__main__":
    app.run(debug=True)
