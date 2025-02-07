#!/usr/bin/env python3

from flask import Flask, request, session, jsonify
from sqlalchemy.exc import IntegrityError
from config import app, db
from models import User, Recipe

# Helper function to format validation errors
def format_validation_errors(errors):
    return {"errors": errors}

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    # Validate incoming data for required fields
    if not data.get('username'):
        return format_validation_errors({"message": "Username is required"}), 422
    if not data.get('password'):
        return format_validation_errors({"message": "Password is required"}), 422
    if not data.get('image_url'):
        return format_validation_errors({"message": "Image URL is required"}), 422
    if not data.get('bio'):
        return format_validation_errors({"message": "Bio is required"}), 422

    try:
        # Create new user with provided data
        new_user = User(
            username=data.get('username'),
            password_hash=data.get('password'),  # Assuming hashing is done elsewhere
            image_url=data.get('image_url'),
            bio=data.get('bio')
        )
        db.session.add(new_user)
        db.session.commit()

        # Save user_id in session
        session['user_id'] = new_user.id

        # Return user data with 201 status code
        return jsonify({
            'id': new_user.id,
            'username': new_user.username,
            'image_url': new_user.image_url,
            'bio': new_user.bio
        }), 201
    except IntegrityError:
        db.session.rollback()
        return format_validation_errors({"message": "Username already taken"}), 422
    except Exception as e:
        # Catch any other exceptions and return 500 with detailed error message
        return format_validation_errors({"message": "An error occurred: " + str(e)}), 500


@app.route('/check_session', methods=['GET'])
def check_session():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            return jsonify({
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }), 200
        return jsonify({"error": "User not found"}), 404
    return jsonify({"error": "Unauthorized"}), 401

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Find user by username
    user = User.query.filter_by(username=username).first()

    if user and user.verify_password(password):
        session['user_id'] = user.id
        return jsonify({
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }), 200
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/logout', methods=['DELETE'])
def logout():
    if 'user_id' in session:
        session.pop('user_id')
        return '', 204
    return jsonify({"error": "Unauthorized"}), 401

@app.route('/recipes', methods=['GET', 'POST'])
def recipes():
    if request.method == 'GET':
        user_id = session.get('user_id')
        if user_id:
            recipes = Recipe.query.filter_by(user_id=user_id).all()
            return jsonify([{
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user': {
                    'id': recipe.user.id,
                    'username': recipe.user.username,
                    'image_url': recipe.user.image_url,
                    'bio': recipe.user.bio
                }
            } for recipe in recipes]), 200
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == 'POST':
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        try:
            new_recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id
            )
            db.session.add(new_recipe)
            db.session.commit()

            return jsonify({
                'title': new_recipe.title,
                'instructions': new_recipe.instructions,
                'minutes_to_complete': new_recipe.minutes_to_complete,
                'user': {
                    'id': new_recipe.user.id,
                    'username': new_recipe.user.username,
                    'image_url': new_recipe.user.image_url,
                    'bio': new_recipe.user.bio
                }
            }), 201
        except IntegrityError:
            db.session.rollback()
            return format_validation_errors({"message": "Recipe validation failed"}), 422
        except Exception as e:
            return format_validation_errors({"message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5555, debug=True)
