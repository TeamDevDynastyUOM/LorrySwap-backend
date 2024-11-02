from flask import jsonify

from app.models import Review
from database import Session
from sqlalchemy import func

def create_review(body) :
    print(body)

    # Print the body of the request to check its contents
    session = Session()

    id = body.get('id')
    ride_id = body.get('ride_id')
    sender = body.get('sender')
    receiver = body.get('receiver')
    rating = body.get('rating')
    title = body.get('title')
    comment = body.get('comment')

    try:
        new_review = Review(
            id = id,
            ride_id = ride_id,
            sender = sender,
            receiver = receiver,
            rating = rating,
            title = title,
            comment = comment
        )

        session.add(new_review)
        session.flush()

        session.commit()
        return True
    except Exception as e:
        print(e)
        session.rollback()
        print(f"Error creating new review")
        return False
    finally:
        session.close()

def get_user_review_stats(user_id):

    session = Session()
    try:

        last_review = session.query(Review).filter(Review.receiver==user_id).order_by(Review.date.desc()).first()
        review_count, rating_count = session.query(
            func.count(Review.id),
            func.count(Review.rating)
        ).filter(Review.receiver == user_id).first()

        # Calculate the average rating
        if rating_count > 0:
            avg_rating = session.query(func.avg(Review.rating)).filter(Review.receiver == user_id).scalar()
        else:
            avg_rating = None

        if last_review:
            review_data = {
                'last_review': {
                    'rating': last_review.rating,
                    'title': last_review.title,
                    'comment': last_review.comment,
                    'date': last_review.date.isoformat()  # Format the date to a string
                },
                'average_rating': avg_rating,
                'rating_count': rating_count,
                'review_count': review_count
            }
        else:
            review_data = {
                'last_review': None,
                'average_rating': avg_rating,
                'rating_count': rating_count,
                'review_count': review_count
            }
        print(review_data)
        return review_data





    except Exception as e:
        print(f"Error retrieving fresh items: {e}")
        return jsonify({"error": "Failed to retrieve fresh items"}), 500

    finally:
        if session:
            session.close()


def get_user_percentage_review(user_id):
    session = Session()
    try:
        # Query for reviews by user ID
        reviews = session.query(Review.rating).filter(Review.receiver == user_id).all()

        # Initialize counters for positive, neutral, and poor ratings
        positive_count = 0
        neutral_count = 0
        poor_count = 0


        # Count ratings based on categories
        for review in reviews:
            if review.rating in [4, 5]:
                positive_count += 1
            elif review.rating in [2, 3]:
                neutral_count += 1
            elif review.rating == 1:
                poor_count += 1

        # Calculate percentages
        total_reviews = len(reviews)




        min_reviews = 5

        # positive_percent = (positive_count / total_reviews) * 100
        # neutral_percent = (neutral_count / total_reviews) * 100
        # poor_percent = (poor_count / total_reviews) * 100
        if total_reviews == 0:
            positive_percent = 0
            neutral_percent = 0
            poor_percent = 0

        elif total_reviews >= min_reviews:
            positive_percent = (positive_count / total_reviews) * 100
            neutral_percent = (neutral_count / total_reviews) * 100
            poor_percent = (poor_count / total_reviews) * 100
        else:
            positive_percent = 0
            neutral_percent = 5
            poor_percent = 0


        # Prepare response data
        response_data = {
            'positive_percent': positive_percent,
            'neutral_percent': neutral_percent,
            'poor_percent': poor_percent,
            'total_reviews': total_reviews
        }

        print(response_data)
        return jsonify({"response":response_data}), 200

    except Exception as e:
        print(f"Error fetching review analysis: {e}")
        return jsonify({'error': 'Failed to fetch review analysis'}), 500

    finally:
        session.close()


