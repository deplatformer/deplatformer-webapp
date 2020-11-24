import os
from datetime import datetime

from flask import flash
from flask_user import current_user
from google.protobuf.json_format import MessageToDict
from pygate_grpc.client import PowerGateClient

from ..app import app, db
from ..crypto import encrypt, encrypt_file
from ..models.filecoin_models import FfsUser, Files, Logs, Wallets


def create_ffs_user() -> FfsUser:
    """
    Create a new Powergate Filecoin Wallet (FFS)
    """

    powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])

    ffs_user = powergate.admin.users.create()

    powergate.set_token(ffs_user.token)

    creation_date = datetime.now().replace(microsecond=0)
    # TODO salt token id
    ffs_user_obj = FfsUser(
        ffs_userid=ffs_user.id,
        token=ffs_user.token,
        creation_date=creation_date,
        user_id=current_user.id,
    )
    db.session.add(ffs_user_obj)

    # Create new FFS wallet and add entry in log table
    address = powergate.wallet.addresses()[0].address
    wallet = Wallets(
        created=creation_date,
        address=address,
        ffs=ffs_user.id,
        user_id=current_user.id,
    )
    db.session.add(wallet)
    db.session.commit()

    return ffs_user_obj


def push_to_filecoin(
    upload_path,
    file_name,
    platform,
):

    # Push file to Filecoin via Powergate
    powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])

    # Retrieve information for default Filecoin FileSystem (FFS)
    ffs_user = FfsUser.query.filter_by(user_id=current_user.id).first()

    if ffs_user is None:
        # No FFS exists yet so create one
        ffs_user = create_ffs_user()

    powergate.set_token(ffs_user.token)

    try:
        # Create an iterator of the uploaded file using the helper function
        filepath = os.path.join(upload_path, file_name)

        # Convert the iterator into request and then add to the hot set (IPFS)
        staged_file = powergate.data.stage_file(filepath)

        # Apply the file to Filecoin
        powergate.config.apply(staged_file.cid)

        # Note the upload date and file size
        upload_date = datetime.now().replace(microsecond=0)
        file_size = os.path.getsize(filepath)

        # Save file information to database
        file_upload = Files(
            file_path=upload_path,
            file_name=file_name,
            upload_date=upload_date,
            file_size=file_size,
            CID=staged_file.cid,
            platform=platform,
            user_id=current_user.id,
            ffs_id=ffs_user.id,
        )
        db.session.add(file_upload)
        db.session.commit()
        print(file_name + " added to Filecoin.")

    except Exception as e:
        # Output error message if pushing to Filecoin fails
        print("Failed to upload {0} to Filecoin.".format(file_name))
        flash(
            "'{}' failed to upload to Filecoin. {}.".format(
                file_name,
                e,
            ),
            "alert-danger",
        )

        # Update log table with error
        event = Logs(
            timestamp=datetime.now().replace(microsecond=0),
            event="Upload ERROR: " + file_name + " " + str(e),
            user_id=current_user.id,
        )
        db.session.add(event)
        db.session.commit()

        # TODO: RESPOND TO SPECIFIC STATUS CODE DETAILS
        # (how to isolate these? e.g. 'status_code.details = ...')

    return ()


def push_dir_to_filecoin(directory, derived_user_key):
    for (
        path,
        subdirectory,
        files,
    ) in os.walk(directory):
        for file in files:
            print(file)
            if file not in [".DS_Store", "thumbs.db", "desktop.ini", ".zip"]:
                filepath = os.path.join(path, file)
                # Encrypt files
                encrypt_file(
                    filepath,
                    derived_user_key,
                    dest=filepath + ".enc"
                )

                # Upload to filecoin
                push_to_filecoin(
                    path,
                    file,
                    "facebook",
                )
