from flask import *
import os
import json

app = Flask(__name__)


def invalid_request(**kwargs):
    return json.dumps(kwargs), 501, {'ContentType': 'application/json'}


def success(**kwargs):
    return json.dumps(kwargs), 200, {'ContentType': 'application/json'}


def update_movie_data(movie_data):
    with open(os.path.join('database', 'MovieScreens.JSON'), 'w+') as database:
        database.write(json.dumps(movie_data))


def read_movie_data():
    with open(os.path.join('database', 'MovieScreens.JSON'), 'r') as database:
        return json.loads(database.read())


@app.route('/')
def show_homepage():
    return render_template('index.html'), 200


@app.route('/screens', methods=['POST'])
def add_movie_screen():
    try:
        movie_data = read_movie_data()
    except Exception as e:
        print(e)
        movie_data = list()

    data = request.get_json()

    for movie in movie_data:
        if movie['name'] == data['name']:
            for seat in data['seatInfo']:
                movie['seatInfo'][seat] = data['seatInfo'][seat]
            break
    else:
        movie_data.append(data)

    update_movie_data(movie_data)
    return success(success=True)


@app.route('/screens/<screen_name>/reserve', methods=['POST'])
def reserve_tickets(screen_name):
    try:
        movie_data = read_movie_data()
    except Exception as e:
        print(e)
        return invalid_request(success=False)

    to_reserve = request.get_json()

    for movie in movie_data:
        if movie['name'] == screen_name:
            if not set(to_reserve["seats"].keys()).issubset(set(movie['seatInfo'].keys())):
                return invalid_request(success=False)
            for seat in to_reserve['seats']:
                if set(to_reserve['seats'][seat]).intersection(set(movie['seatInfo'][seat]['aisleSeats'])) \
                        or not set(to_reserve['seats'][seat]) \
                        .issubset(set(list(range(movie['seatInfo'][seat]['numberOfSeats'])))):
                    return invalid_request(success=False)
                movie['seatInfo'][seat]['aisleSeats'] += to_reserve['seats'][seat]
            update_movie_data(movie_data)
            return success(success=True)
    else:
        return invalid_request(success=False)


@app.route('/screens/<screen_name>/seats', methods=['GET'])
def available_seats(screen_name):
    try:
        movie_data = read_movie_data()
        for movie in movie_data:
            if movie['name'] == screen_name:
                seat_info = movie['seatInfo']
                break
        else:
            return invalid_request(success=False, seats=dict())
    except Exception as e:
        print(e)
        return invalid_request(success=False, seats=dict())

    seats = dict()

    try:
        status = request.args['status']
        if status == 'unreserved':
            for seat in seat_info:
                seats[seat] = [i for i in range(seat_info[seat]['numberOfSeats']) if
                               i not in seat_info[seat]['aisleSeats']]
            return success(seats=seats)
        else:
            return invalid_request(success=False, seats=dict())
    except KeyError:
        try:
            num_seats, choice_row, choice_seat = int(request.args['numSeats']), request.args['choice'][:1], \
                                                 int(request.args['choice'][1:])
            try:
                aisle_seats = set(seat_info[choice_row]['aisleSeats'])
            except KeyError:
                return invalid_request(success=False, availableSeats={choice_row: []})

            for i in range(choice_seat - num_seats + 1, choice_seat + 1):
                for j in range(i, i + num_seats):
                    if j in aisle_seats or j not in range(seat_info[choice_row]['numberOfSeats']):
                        break
                else:
                    return success(availableSeats={choice_row: list(range(i, i + num_seats))})
            return invalid_request(success=False, availableSeats={choice_row: []})
        except KeyError:
            return render_template('404.html'), 404
        except ValueError:
            return invalid_request(success=False, seats=dict())


@app.errorhandler(404)
def page_not_found(e):
    print(e)
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=True)
