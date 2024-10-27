from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Sample data structure for seats (you would normally fetch this from a database)
seats = [
    {'number': 1, 'available': True},
    {'number': 2, 'available': True},
    {'number': 3, 'available': False},
    # Add more seats as needed...
]

@app.route('/available-seats/<int:bus_id>', methods=['GET'])
def available_seats(bus_id):
    # Fetch available seats for the given bus_id from the database
    return render_template('available_seats.html', bus_id=bus_id, seats=seats)

@app.route('/book-seat', methods=['POST'])
def book_seat():
    data = request.get_json()
    seat_number = data.get('seat_number')
    bus_id = data.get('bus_id')

    # Logic to book the seat
    for seat in seats:
        if seat['number'] == seat_number:
            if seat['available']:
                seat['available'] = False  # Mark as booked
                return jsonify({'message': f'Seat {seat_number} successfully booked!'}), 200
            else:
                return jsonify({'message': 'Seat is already booked!'}), 400

    return jsonify({'message': 'Seat not found!'}), 404

if __name__ == '__main__':
    app.run(debug=True)
