# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
from datetime import datetime
import sys
import os
# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)
# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String())
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(), default='Null')

    # parent class relationship
    venue = db.relationship('Shows', backref='venue',
                            cascade="all, delete-orphan", lazy=True)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

    def __repr__(self):
        return f'<Venue {self.id} {self.name} {self.city} {self.state}>'


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    seeking_venues = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(
        db.String(), default='Null')

    # parent class relation ship
    artist = db.relationship('Shows', backref='artist', lazy=True)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Shows(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime
current_date_time = str(datetime.now())
# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    try:
        venues_data = Venue.query.distinct(Venue.city).all()
        data = []

        for row in venues_data:
            related_venues = Venue.query.filter_by(city=row.city).all()
            num_upcoming_shows = Shows.query.filter_by(venue_id=row.id).where(
                Shows.start_time > current_date_time).count()
            ven_list = []
            for r in related_venues:
                ven_list += [
                    {
                        "id": r.id,
                        "name": r.name,
                        "num_upcoming_shows": num_upcoming_shows
                    }
                ]
                data += [{
                    "city": row.city,
                    "state": row.state,
                    "venues": ven_list
                }]
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        return render_template('pages/venues.html', areas=data)
        # return data


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.like('%{t}%'.format(t=term))).all()
    count_venues = Venue.query.filter(
        Venue.name.like('%{t}%'.format(t=term))).count()
    search_data = []

    for row in venues:
        num_upcoming_shows = Shows.query.filter_by(venue_id=row.id).where(
            Shows.start_time > current_date_time).count()
        search_data += [{
            "id": row.id,
            "name": row.name,
            "num_upcoming_shows": num_upcoming_shows
        }]

    response = {
        "count": count_venues,
        "data": search_data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    upcoming_shows = []
    past_shows = []

    # genres data into list
    venue_genres = venue.genres
    venue_genres = venue_genres.translate({ord('{'): None})
    venue_genres = venue_genres.translate({ord('}'): None})
    genres = venue_genres.split(",")
    print(genres)
    # upcoming shows query
    up_shows_query = Shows.query.with_entities(Shows.artist_id, Artist.name, Artist.image_link, Shows.start_time).filter_by(
        venue_id=venue_id).where(Shows.start_time > current_date_time).join(Artist).all()
    pa_shows_query = Shows.query.with_entities(Shows.artist_id, Artist.name, Artist.image_link, Shows.start_time).filter_by(
        venue_id=venue_id).where(Shows.start_time < current_date_time).join(Artist).all()
    upcoming_shows_count = Shows.query.with_entities(Shows.artist_id, Artist.name, Artist.image_link, Shows.start_time).filter_by(
        venue_id=venue_id).where(Shows.start_time > current_date_time).join(Artist).count()
    past_shows_count = Shows.query.with_entities(Shows.artist_id, Artist.name, Artist.image_link, Shows.start_time).filter_by(
        venue_id=venue_id).where(Shows.start_time < current_date_time).join(Artist).count()

    for row in up_shows_query:
        upcoming_shows += [{
            "artist_id": row.artist_id,
            "artist_name": row.name,
            "artist_image_link": row.image_link,
            "start_time": str(row.start_time)
        }]

    for row in pa_shows_query:
        past_shows += [{
            "artist_id": row.artist_id,
            "artist_name": row.name,
            "artist_image_link": row.image_link,
            "start_time": str(row.start_time)
        }]

        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website_link,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": past_shows_count,
            "upcoming_shows_count": upcoming_shows_count,
        }
        return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    seeking_talent_bool = False
    # TODO: insert form data as a new Venue record in the db, instead
    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        address = request.form.get('address')
        phone = request.form.get('phone')
        genres = request.form.getlist('genres')
        facebook_link = request.form.get('facebook_link')
        image_link = request.form.get('image_link')
        website_link = request.form.get('website_link')
        seeking_talent = request.form.get('seeking_talent')
        seeking_description = request.form.get('seeking_description')
        if seeking_talent == 'None':
            seeking_talent_bool = False
        elif seeking_talent == 'True':
            seeking_talent_bool = True

        venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            genres=genres,
            facebook_link=facebook_link,
            image_link=image_link,
            website_link=website_link,
            seeking_talent=seeking_talent_bool,
            seeking_description=seeking_description
        )

        db.session.add(venue)
        db.session.flush()
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
        return

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    artists = Artist.query.with_entities(Artist.id, Artist.name).all()
    data = []
    for row in artists:
        data += [{
            "id": row.id,
            "name": row.name
        }]
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    term = request.form.get('search_term', '')
    artists = Artist.query.filter(
        Artist.name.like('%{t}%'.format(t=term))).all()
    count_artist = Artist.query.filter(
        Artist.name.like('%{t}%'.format(t=term))).count()
    search_data = []

    for row in artists:
        num_upcoming_shows = Shows.query.filter_by(artist_id=row.id).where(
            Shows.start_time > current_date_time).count()
        search_data += [{
            "id": row.id,
            "name": row.name,
            "num_upcoming_shows": num_upcoming_shows
        }]

    response = {
        "count": count_artist,
        "data": search_data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.get(artist_id)
    print(artist.seeking_venues)
    upcoming_shows = []
    past_shows = []

    # genres data into list
    artist_genres = artist.genres
    artist_genres = artist_genres.translate({ord('{'): None})
    artist_genres = artist_genres.translate({ord('}'): None})
    genres = artist_genres.split(",")

    # upcoming shows query
    up_shows_query = Shows.query.with_entities(Shows.artist_id, Venue.name, Venue.image_link, Shows.start_time).filter_by(
        artist_id=artist_id).where(Shows.start_time > current_date_time).join(Venue).all()
    pa_shows_query = Shows.query.with_entities(Shows.artist_id, Venue.name, Venue.image_link, Shows.start_time).filter_by(
        artist_id=artist_id).where(Shows.start_time < current_date_time).join(Venue).all()

    upcoming_shows_count = Shows.query.with_entities(Shows.artist_id, Venue.name, Venue.image_link, Shows.start_time).filter_by(
        artist_id=artist_id).where(Shows.start_time > current_date_time).join(Venue).count()
    past_shows_count = Shows.query.with_entities(Shows.artist_id, Venue.name, Venue.image_link, Shows.start_time).filter_by(
        artist_id=artist_id).where(Shows.start_time > current_date_time).join(Venue).count()

    for row in up_shows_query:
        upcoming_shows += [{
            "venue_id": row.artist_id,
            "venue_name": row.name,
            "venue_image_link": row.image_link,
            "start_time": str(row.start_time)
        }]

    for row in pa_shows_query:
        past_shows += [{
            "venue_id": row.artist_id,
            "venue_name": row.name,
            "venue_image_link": row.image_link,
            "start_time": str(row.start_time)
        }]

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": genres,
        # "address": artist.address,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venues,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": past_shows_count,
        "upcoming_shows_count": upcoming_shows_count,
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    # genres data into list
    artist_genres = artist.genres
    artist_genres = artist_genres.translate({ord('{'): None})
    artist_genres = artist_genres.translate({ord('}'): None})
    genres = artist_genres.split(",")

    artist = {
        "id": artist.id,
        "name": artist.name,
        "genres": genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venues": artist.seeking_venues,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        artist = Artist.query.get(artist_id)
        old_artist_name = artist.name
        seeking_venue = request.form.get('seeking_venue')
        seeking_venue_bool = False

        if seeking_venue == 'None' or seeking_venue == 'y' or seeking_venue == 'False':
            seeking_venue_bool = False
        elif seeking_venue == 'True':
            seeking_venue_bool = True

        db.session.query(Artist).filter(Artist.id == artist.id).update({
            Artist.name: request.form.get('name'),
            Artist.state: request.form.get('state'),
            Artist.city: request.form.get('city'),
            Artist.phone: request.form.get('phone'),
            Artist.genres: request.form.getlist('genres'),
            Artist.facebook_link: request.form.get('facebook_link'),
            Artist.image_link: request.form.get('image_link'),
            Artist.website_link: request.form.get('website_link'),
            Artist.seeking_venues: seeking_venue_bool,
            Artist.seeking_description: request.form.get('seeking_description')
        }, synchronize_session=False)

        db.session.commit()
        flash('Artist ' + old_artist_name + ' was successfully updated!')
    except:
        print('Artist Updating failed')
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()
        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    # genres data into list
    venue_genres = venue.genres
    venue_genres = venue_genres.translate({ord('{'): None})
    venue_genres = venue_genres.translate({ord('}'): None})
    genres = venue_genres.split(",")

    venue = {
        "id": venue.id,
        "name": venue.name,
        "genres": genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
        venue = Venue.query.get(venue_id)
        old_venue_name = venue.name
        seeking_talent = request.form.get('seeking_talent')
        seeking_talent_bool = False
        print(seeking_talent)
        if seeking_talent == 'None':
            seeking_talent_bool = False
        elif seeking_talent == 'True':
            seeking_talent_bool = True

        db.session.query(Venue).filter(Venue.id == venue.id).update({
            Venue.name: request.form.get('name'),
            Venue.state: request.form.get('state'),
            Venue.city: request.form.get('city'),
            Venue.address: request.form.get('address'),
            Venue.phone: request.form.get('phone'),
            Venue.genres: request.form.getlist('genres'),
            Venue.facebook_link: request.form.get('facebook_link'),
            Venue.image_link: request.form.get('image_link'),
            Venue.website_link: request.form.get('website_link'),
            Venue.seeking_talent: seeking_talent_bool,
            Venue.seeking_description: request.form.get('seeking_description')
        }, synchronize_session=False)

        db.session.commit()
        flash('Venue ' + old_venue_name + ' was successfully updated!')
    except:
        db.session.rollback()
    finally:
        db.session.close()
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    seeking_venue_bool = False
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        phone = request.form.get('phone')
        genres = request.form.getlist('genres')
        facebook_link = request.form.get('facebook_link')
        image_link = request.form.get('image_link')
        website_link = request.form.get('website_link')
        seeking_venue = request.form.get('seeking_venue')
        seeking_description = request.form.get('seeking_description')
        if seeking_venue == 'None':
            seeking_venue_bool = False
        elif seeking_venue == 'True':
            seeking_venue_bool = True
        # print(seeking_venue_bool)
        artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=genres,
            facebook_link=facebook_link,
            image_link=image_link,
            website_link=website_link,
            seeking_venues=seeking_venue_bool,
            seeking_description=seeking_description
        )

        db.session.add(artist)
        db.session.flush()
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = []
    shows = Shows.query.all()

    for row in shows:
        data += [{
            "venue_id": row.venue_id,
            "venue_name": "",
            "artist_id": row.artist_id,
            "artist_name": "",
            "artist_image_link": "",
            "start_time": str(row.start_time)
        }]

    artist = Artist.query.with_entities(Artist.name, Artist.image_link).filter_by(id=Shows.artist_id).join(Shows).all()
    for i in range(len(data)):
        for row in artist:
            data[i]["artist_name"] = row.name,
            data[i]["artist_image_link"] = row.image_link
            

    venue = Venue.query.with_entities(Venue.name).where(Shows.venue_id == Venue.id).join(Shows).all()
    for i in range(len(data)):
        for row in venue:
            data[i]["venue_name"] = row.name
            
    return render_template('pages/shows.html', shows=data)



@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False

    try:
        artist_id = request.form.get('artist_id')
        venue_id = request.form.get('venue_id')
        start_time = request.form.get('start_time')

        artists = db.session.query(Artist).filter(
            Artist.id == artist_id).count()
        venues = db.session.query(Venue).filter(Venue.id == venue_id).count()

        if (artists == 1 and venues == 1):
            show = Shows(
                artist_id=artist_id,
                venue_id=venue_id,
                start_time=format_datetime(start_time, 'full')
            )
            db.session.add(show)
            db.session.flush()
            db.session.commit()
            flash('Show was successfully listed!')
        else:
            flash('An error occurred. Show could not be listed.')

    except:
        error = True
        # db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
