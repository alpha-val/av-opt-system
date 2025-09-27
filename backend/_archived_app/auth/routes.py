from ..core.model import get_collection, to_json
from bson.objectid import ObjectId
from datetime import datetime
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, g, current_app as app
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from jwt import DecodeError, ExpiredSignatureError
import jwt
import os

auth_bp = Blueprint("auth", __name__)

# Collections accessed
COL_USERS = get_collection("users")
COL_INVITES = get_collection("invites")

# Role definitions
VALID_ROLES = {"parent", "athlete", "coach", "admin", "super_admin"}

# Configuration for JWT
JWT_EXPIRY_MINUTES = 60 * 24  # 1 day


# ─────────────────────────────────────────────────────────────────────────────
def require_auth(fn):
    """Small decorator that decodes the Bearer token and attaches g.user"""

    @wraps(fn)
    def wrapped(*args, **kw):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return jsonify({"message": "Auth token missing"}), 401
        try:
            claims = jwt.decode(token, app.secret_key, algorithms=["HS256"])
        except (DecodeError, ExpiredSignatureError):
            return jsonify({"message": "Invalid or expired token"}), 401

        user = COL_USERS.find_one({"_id": ObjectId(claims["user_id"])})
        if not user:
            return jsonify({"message": "User not found"}), 401
        g.user = user
        g.claims = claims
        return fn(*args, **kw)

    return wrapped


# ─────────────────────────────────────────────────────────────────────────────
# Get date-time
def now_utc():
    return datetime.now(timezone.utc)  # naive—Mongo treats as UTC


# ─────────────────────────────────────────────────────────────────────────────
# Create JWT token for a user
def create_jwt(user):
    payload = {
        "user_id": str(user["userId"]),
        "email": user["email"],
        "role": user.get("role", "parent"),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, app.secret_key, algorithm="HS256")


# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/users", methods=["GET"])
def get_all_users():
    users = get_collection("users").find()
    return jsonify([to_json(u) for u in users])


def checkIfUserEmailExists(email, db_collection_obj):
    doesUserExist = db_collection_obj.find_one({"email": email})

    return doesUserExist


def getPasswordHash(password):
    return generate_password_hash(password, method="pbkdf2:sha256")


def new_tenant_id() -> ObjectId:
    return ObjectId()


# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True) or {}

    # -------- 1. Field validation -------------------------------------------
    missing = [
        k for k in ("firstName", "lastName", "email", "password") if not data.get(k)
    ]
    if missing:
        return jsonify({"message": f"Missing fields: {', '.join(missing)}"}), 400

    role = data.get("role", "").strip().lower()
    if role not in VALID_ROLES:
        return jsonify({"message": "Invalid role"}), 400

    email = data["email"].strip().lower()

    # -------- 2. Determine tenantId -----------------------------------------
    invite_token = data.get("inviteToken")
    if invite_token:
        tok = COL_INVITES.find_one({"_id": ObjectId(invite_token), "redeemed": False})
        if not tok:
            return jsonify({"message": "Invalid or expired invite"}), 400
        tenant_id = tok["tenantId"]  # reuse family/club ID
    else:
        tenant_id = ObjectId()  # new family circle

    # -------- 3. Find-or-create user row ------------------------------------
    user = COL_USERS.find_one({"email": email})

    if user:
        # Existing account → just add tenant if missing
        COL_USERS.update_one(
            {"_id": user["_id"]},
            {"$addToSet": {"tenantIds": tenant_id}, "$set": {"updatedAt": now_utc()}},
        )
        user_id = user["_id"]
        tenant_ids = set(user["tenantIds"]) | {tenant_id}
        role_final = user["role"]  # cannot change here
    else:
        # -------- 3a. Build fresh doc (minimal) -----------------------------
        profiles = {
            "parent": {
                "athleteIds": [],
                "coachIds": [],
                "phone": None,
                "address": None,
            },
            "athlete": {
                "parentIds": [],
                "coachIds": [],
                "birthYear": None,
                "playGroup": "",
                "currentOrg": "",  # Current club name
                "currentTeam": "",  # Current team name
            },
            "coach": {"athleteIds": [], "certifications": []},
        }

        new_doc = {
            "tenantIds": [tenant_id],
            "role": role,
            "email": email,
            "firstName": data["firstName"].strip(),
            "lastName": data["lastName"].strip(),
            "passwordHash": getPasswordHash(data["password"]),
            "status": "active",
            "createdAt": now_utc(),
            "updatedAt": now_utc(),
            f"{role}Profile": profiles[role],
        }

        try:
            res = COL_USERS.insert_one(new_doc)
            user_id = res.inserted_id
            tenant_ids = {tenant_id}
            role_final = role
        except DuplicateKeyError:
            # very unlikely race—retry path that appends tenant
            user = COL_USERS.find_one({"email": email})
            user_id = user["_id"]
            tenant_ids = set(user["tenantIds"]) | {tenant_id}
            role_final = user["role"]

    # -------- 4. Mark invite token redeemed (if any) -------------------------
    if invite_token:
        COL_INVITES.update_one({"_id": tok["_id"]}, {"$set": {"redeemed": True}})

        # ---- link coach to athlete & parents --------------------------------
        if role_final == "coach" and tok.get("targetAthleteId"):
            coach_id = user_id
            athlete_oid = tok["targetAthleteId"]

            # 1) add coach to the athlete
            COL_USERS.update_one(
                {"_id": athlete_oid, "role": "athlete"},
                {"$addToSet": {"athleteProfile.coachIds": coach_id}},
            )

            # 2) add coach to each parent of that athlete
            athlete = COL_USERS.find_one(
                {"_id": athlete_oid}, {"athleteProfile.parentIds": 1}
            )
            for parent_oid in athlete["athleteProfile"]["parentIds"]:
                COL_USERS.update_one(
                    {"_id": parent_oid, "role": "parent"},
                    {"$addToSet": {"parentProfile.coachIds": coach_id}},
                )
    # -------- 5. Issue JWT ---------------------------------------------------
    jwt_token = create_jwt(
        {
            "userId": str(user_id),
            "email": user["email"],
            "role": role_final,
            "tenantIds": [str(t) for t in tenant_ids],
            "defaultTenant": str(tenant_id),  # context user just joined
        }
    )

    # -------- 6. Success response -------------------------------------------
    return (
        jsonify(
            {
                "token": jwt_token,
                "user": {
                    "_id": str(user_id),
                    "firstName": data["firstName"].strip(),
                    "lastName": data["lastName"].strip(),
                    "email": email,
                    "role": role_final,
                    "tenantIds": [str(t) for t in tenant_ids],
                },
            }
        ),
        201,
    )


# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    print(f"[Debug] Login attempt for email: {email}, {password}")
    # --- basic input guard ---------------------------------------------------
    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400

    # --- locate user ---------------------------------------------------------
    user = COL_USERS.find_one({"email": email})
    if not user or not user.get("passwordHash"):
        return jsonify({"message": "Invalid email or password"}), 401

    # --- verify password -----------------------------------------------------
    if not check_password_hash(user["passwordHash"], password):
        return jsonify({"message": "Invalid email or password"}), 401

    # --- issue JWT -----------------------------------------------------------
    jwt_token = create_jwt(
        {
            "userId": str(user["_id"]),
            "role": user["role"],
            "email": user["email"],
        }
    )

    # --- success payload -----------------------------------------------------
    return (
        jsonify(
            {
                "token": jwt_token,
                "user": {
                    "_id": str(user["_id"]),
                    "firstName": user["firstName"],
                    "lastName": user["lastName"],
                    "email": user["email"],
                    "role": user["role"],
                },
            }
        ),
        200,
    )


# @auth_bp.route("/register_stepper", methods=["POST"])
# def register_stepper():
#     data = request.json
#     parent = data.get("parentData")
#     athletes = data.get("athletesData")

#     print("Parent>", parent)
#     print("Athletes > ", athletes)
#     if not parent:
#         return jsonify({"message", "Parent login information is missing"}), 400
#     if not athletes:
#         return jsonify({"message", "Athlete information is missing"}), 400

#     # Prepare to save parent information
#     parent_to_insert = {
#         "firstName": parent["firstName"],
#         "lastName": parent["lastName"],
#         "email": parent["email"],
#         "role": parent["role"] or "parent",
#         "athleteIds": [],
#         "coachIds": [],
#         "createdAt": datetime.now(timezone.utc),
#         "passwordHash": generate_password_hash(
#             parent["password"], method="pbkdf2:sha256"
#         ),
#         "tenantId": "",
#         "updatedAt": datetime.now(timezone.utc),
#     }
#     print("Parent to insert: ", parent_to_insert)
#     return (
#         jsonify(
#             {
#                 "token": None,
#                 "user": {},
#             }
#         ),
#         200,
#     )


# @auth_bp.route("/register", methods=["POST"])
# def register():
#     data = request.json
#     print("Data received> ", data)
#     firstName = data.get("firstName")
#     lastName = data.get("lastName")
#     email = data.get("email")
#     password = data.get("password")
#     role = data.get("role", "").strip().lower()

#     if not firstName or not lastName:
#         return jsonify({"message": "First and last names required"}), 400

#     if not email or not password:
#         return jsonify({"message": "Email and password required"}), 400

#     # Get the appropriate collection
#     _collection = get_collection("users")

#     # Ensure the user is unique
#     userExists = checkIfUserEmailExists(email, _collection)
#     if userExists:
#         return jsonify({"message": "Email already registered"}), 409

#     # Generate a hash to store password securely
#     password_hash = getPasswordHash(password)

#     # Create the user document to be store in the collection 'users'
#     user_doc = {
#         # Key attributes
#         "email": email,
#         "firstName": firstName,
#         "lastName": lastName,
#         "password_hash": password_hash,
#         # Record keeping
#         "createdAt": datetime.now(timezone.utc),
#         "updatedAt": datetime.now(timezone.utc),
#         # Organizations
#         "groupId": "",  # association with a group; e.g., team 14U
#         # Status
#         "profileStatus": "active",  # "active" | "suspended" | "deleted"
#     }

#     # Role-specific data
#     if role == "parent":
#         print("[Debug] Registering a parent.")
#         user_doc["parentData"] = {
#             "tenantId": new_tenant_id(),  # association with a club or school; e.g., NCVBA
#             # Contact
#             "phone": "",
#             "address": "",
#             # Connections
#             "athleteIds": [],  # connected athletes
#             "coachIds": [],  # connected coaches
#         }

#     elif role == "athlete":
#         user_doc["athleteData"] = {
#             "tenantId": new_tenant_id(),  # association with a club or school; e.g., NCVBA
#         }
#     elif role == "coach":
#         user_doc["coachData"] = {
#             "tenantId": new_tenant_id(),  # association with a club or school; e.g., NCVBA
#         }
#     else:
#         return (
#             jsonify(
#                 {"message": "Error registering the user: user role empty or not valid"}
#             ),
#             400,
#         )
#     res = _collection.insert_one(user_doc)
#     user_doc["_id"] = res.inserted_id

#     token = create_jwt(user_doc)
#     # Successfully added the user
#     print("[Debug] Registration successful.")
#     return (
#         jsonify(
#             {
#                 "token": token,
#                 "user": {
#                     "firstName": firstName,
#                     "lastName": lastName,
#                     "email": email,
#                     "role": role,
#                     "_id": str(user_doc["_id"]),
#                 },
#             }
#         ),
#         201,
#     )


# @auth_bp.route("/login", methods=["POST"])
# def login():
#     data = request.json
#     users = get_collection("users")
#     email = data.get("email")
#     password = data.get("password")

#     user = users.find_one({"email": email})
#     if not user or not check_password_hash(user.get("password_hash", ""), password):
#         return jsonify({"message": "Invalid email or password"}), 401

#     token = create_jwt(user)
#     return (
#         jsonify(
#             {
#                 "token": token,
#                 "user": {
#                     "name": user["name"],
#                     "email": user["email"],
#                     "role": user.get("role", "parent"),
#                     "_id": str(user["_id"]),
#                 },
#             }
#         ),
#         200,
#     )


@auth_bp.route("/logout", methods=["POST"])
def logout():
    # For JWT, logout is handled client-side by deleting the token.
    # Optionally, you can implement token blacklisting here.
    return jsonify({"message": "Logged out"}), 200
