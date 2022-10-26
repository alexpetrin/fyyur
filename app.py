#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from datetime import datetime
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref='show_venue', lazy=True, cascade='all, delete')
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    website = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='show_artist', lazy=True, cascade='all, delete')

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id', ondelete='cascade'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id', ondelete='cascade'))
    start_time = db.Column(db.DateTime)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  error = False
  try:
    areas = Venue.query.with_entities(Venue.city, Venue.state).distinct()
    data = []
    entry = []
    for area in areas:
      venue_data = []
      venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city)
      for venue in venues:
        upcoming_shows = Show.query.filter_by(venue_id=venue.id).count()
        venue_data.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': upcoming_shows
        })
      entry.append({
      'city': area.city,
      'state': area.state,
      'venues' : venue_data
      })
    data = entry
  except Exception as e:
    print('Error building venues: ',e)
    for area in areas:
      print(area)
      error = True
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))
  data = []
  count = 0
  for venue in venues:
    count += 1
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": Show.query.filter_by(venue_id=venue.id).count(),      
    })
  response = {
    "count": count,
    "data": data,
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  error = False
  try:
      data = []
      venue = Venue.query.get(venue_id)
      shows = Show.query.filter_by(venue_id=venue_id)
      past_data = []
      upcoming_data = []
      past_count = 0
      upcoming_count = 0
      for show in shows:
          artist = Artist.query.get(show.artist_id)
          show_data = {
              "artist_id": show.artist_id,
              "artist_name": artist.name,
              "artist_image_link": artist.image_link,
              "start_time": format_datetime(str(show.start_time)),        
          }
          if show.start_time < datetime.now():
              past_data.append(show_data)
              past_count += 1
          else:
              upcoming_data.append(show_data)
              upcoming_count += 1
      
      data = {
          "id": venue.id,
          "name": venue.name,
          "genres": venue.genres,
          "address": venue.address,
          "city": venue.city,
          "state": venue.state,
          "phone": venue.phone,
          "website": venue.website,
          "facebook_link": venue.facebook_link,
          "seeking_talent": venue.seeking_talent,
          "seeking_description": venue.seeking_description,
          "image_link": venue.image_link,
          "past_shows": past_data,
          "upcoming_shows": upcoming_data,
          "past_shows_count": past_count,
          "upcoming_shows_count": upcoming_count,
      }
  except Exception as e:
    print('Error building venue: ',e)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
      try:
        if request.form['seeking_talent'] == 'y':
          seeking_talent = True
      except:
        seeking_talent = False
      venue = Venue(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        address = request.form['address'],
        phone = request.form['phone'],
        genres = request.form.getlist('genres'),
        facebook_link = request.form['facebook_link'],
        image_link = request.form['image_link'],
        website = request.form['website_link'],
        seeking_talent = seeking_talent,
        seeking_description = request.form['seeking_description'],
      )
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
  try: 
      Venue.query.filter_by(id=venue_id).delete()
      db.session.commit()
      flash('Venue was Deleted')
  except:        
      db.session.rollback()
      flash('Venue was Not Deleted')
  finally:
      db.session.close()
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data=[]
  artists = Artist.query.all()
  for artist in artists:
    data.append({
        "id": artist.id,
        "name": artist.name,      
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
  data = []
  count = 0
  for artist in artists:
    count += 1
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": Show.query.filter_by(artist_id=artist.id).filter(Show.start_time >= datetime.now()).count(),      
    })
  response = {
    "count": count,
    "data": data,
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  past_data = []
  upcoming_data = []
  past_count = 0
  upcoming_count = 0
  artist = Artist.query.get(artist_id)
  shows = Show.query.filter_by(artist_id=artist_id)
  for show in shows:
    venue = Venue.query.get(show.venue_id)
    show_data = {
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": format_datetime(str(show.start_time)),
    }
    if show.start_time < datetime.now():
        past_data.append(show_data)
        past_count += 1
    else:
        upcoming_data.append(show_data)
        upcoming_count += 1
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_data,
    "upcoming_shows": upcoming_data,
    "past_shows_count": past_count,
    "upcoming_shows_count": upcoming_count,
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
      artist = Artist.query.get(artist_id)
      try:
        if request.form['seeking_venue'] == 'y':
          seeking_venue = True
      except:
        seeking_venue = False
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form.getlist('genres')
      artist.facebook_link = request.form['facebook_link']
      artist.image_link = request.form['image_link']
      artist.website = request.form['website_link']
      artist.seeking_venue = seeking_venue
      artist.seeking_description = request.form['seeking_description']
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
      venue = Venue.query.get(venue_id)
      try:
        if request.form['seeking_talent'] == 'y':
          seeking_talent = True
      except:
        seeking_talent = False
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.genres = request.form.getlist('genres')
      venue.facebook_link = request.form['facebook_link']
      venue.image_link = request.form['image_link']
      venue.website = request.form['website_link']
      venue.seeking_talent = seeking_talent
      venue.seeking_description = request.form['seeking_description']
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
      db.session.rollback()
      print(sys.exc_info())
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
  try:
      try:
        if request.form['seeking_venue'] == 'y':
          seeking_venue = True
      except:
        seeking_venue = False
      artist = Artist(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        phone = request.form['phone'],
        genres = request.form.getlist('genres'),
        facebook_link = request.form['facebook_link'],
        image_link = request.form['image_link'],
        website = request.form['website_link'],
        seeking_venue = seeking_venue,
        seeking_description = request.form['seeking_description'],
      )
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
      # on failed db insert, flash error
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data=[]
  shows = Show.query.all()
  for show in shows:
    venue = Venue.query.get(show.venue_id)
    artist = Artist.query.get(show.artist_id)
    data.append({
      "venue_id": show.venue_id,
      "venue_name": venue.name,
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
      show = Show(
        artist_id = request.form['artist_id'],
        venue_id = request.form['venue_id'],
        start_time = request.form['start_time'],
      )
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')
  except:
      flash('An error occurred. Show could not be listed.')
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
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
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
