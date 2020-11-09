import os
from datetime import datetime

from flask import flash
from flask_user import current_user
from google.protobuf.json_format import MessageToDict
from pygate_grpc.client import PowerGateClient
from pygate_grpc.ffs import bytes_to_chunks, chunks_to_bytes, get_file_bytes

from ..app import app, db
from ..models.filecoin_models import Ffs, Files, Logs, Wallets


def create_ffs():
    """
    Create a new Powergate Filecoin Filesystem (FFS)
    """

    powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])

    ffs = powergate.ffs.create()
    creation_date = datetime.now().replace(microsecond=0)
    # TODO salt token id
    filecoin_file_system = Ffs(
        ffs_id=ffs.id,
        token=ffs.token,
        creation_date=creation_date,
        user_id=current_user.id,
    )
    db.session.add(filecoin_file_system)

    # Create new FFS wallet and add entry in log table
    address = powergate.ffs.addrs_list(ffs.token)
    obj = MessageToDict(address)
    wallet = obj["addrs"][0]["addr"]
    wallet = Wallets(
        created=creation_date,
        address=wallet,
        ffs=ffs.id,
        user_id=current_user.id,
    )
    db.session.add(wallet)
    db.session.commit()

    new_ffs = Ffs.query.filter_by(ffs_id=ffs.id).first()

    return new_ffs


def push_to_filecoin(
    upload_path,
    file_name,
    platform,
):

    # Push file to Filecoin via Powergate
    powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])

    # Retrieve information for default Filecoin FileSystem (FFS)
    ffs = Ffs.query.filter_by(user_id=current_user.id).first()

    if ffs is None:
        # No FFS exists yet so create one
        ffs = create_ffs()

    try:
        # Create an iterator of the uploaded file using the helper function
        file_iterator = get_file_bytes(
            os.path.join(
                upload_path,
                file_name,
            )
        )

        # Convert the iterator into request and then add to the hot set (IPFS)
        file_hash = powergate.ffs.stage(
            bytes_to_chunks(file_iterator),
            ffs.token,
        )

        # Push the file to Filecoin
        powergate.ffs.push(
            file_hash.cid,
            ffs.token,
        )

        # Note the upload date and file size
        upload_date = datetime.now().replace(microsecond=0)
        file_size = os.path.getsize(
            os.path.join(
                upload_path,
                file_name,
            )
        )

        # Save file information to database
        file_upload = Files(
            file_path=upload_path,
            file_name=file_name,
            upload_date=upload_date,
            file_size=file_size,
            CID=file_hash.cid,
            platform=platform,
            user_id=current_user.id,
            ffs_id=ffs.id,
        )
        db.session.add(file_upload)
        db.session.commit()
        print(file_name + " added to Filecoin.")

    except Exception as e:
        # Output error message if pushing to Filecoin fails
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
