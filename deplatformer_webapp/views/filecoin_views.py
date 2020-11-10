import os
from datetime import datetime

from flask import flash, render_template, safe_join, send_file
from flask_user import current_user, login_required
from pygate_grpc.client import PowerGateClient

from ..app import app, db
from ..models.filecoin_models import Ffs, Files, Logs


@app.route("/filecoin-files")
@login_required
def filecoin_files():

    files = Files.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "filecoin/filecoin-files.html",
        files=files,
        breadcrumb="Filecoin / Files",
    )


@app.route(
    "/filecoin-download/<cid>",
    methods=["GET"],
)
@login_required
def filecoin_download(
    cid,
):
    """
    Retrieve a file from Filecoin via IPFS using Powergate and offer the user
    the option to save it to their machine.
    """

    # Retrieve File and FFS info using the CID
    file = Files.query.filter_by(
        CID=cid,
        user_id=current_user.id,
    ).first()
    ffs = Ffs.query.get(file.ffs_id)

    try:
        # Retrieve data from Filecoin
        powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])
        data_ = powergate.ffs.get(
            file.CID,
            ffs.token,
        )

        # Save the downloaded data as a file
        # Use the user data directory configured for the app
        user_data = app.config["USER_DATA_DIR"]
        if not os.path.exists(user_data):
            os.makedirs(user_data)

        print(user_data)
        # Create a subdirectory per username. Usernames are unique.
        user_dir = os.path.join(
            user_data,
            str(current_user.id) + "-" + current_user.username,
        )
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        print(user_dir)
        # Create a Filecoin downloads subdirectory.
        filecoin_dir = os.path.join(
            user_dir,
            "filecoin/downloads",
        )
        if not os.path.exists(filecoin_dir):
            os.makedirs(filecoin_dir)
        print(filecoin_dir)
        with open(
            os.path.join(
                filecoin_dir,
                file.file_name,
            ),
            "wb",
        ) as out_file:
            # Iterate over the data byte chunks and save them to an output file
            for data in data_:
                out_file.write(data)

        # Create path to download file
        safe_path = safe_join(
            "../" + filecoin_dir,
            file.file_name,
        )
        print(safe_path)

        # Offer the file for download to local machine
        return send_file(
            safe_path,
            as_attachment=True,
        )

        # TODO: CLEAR CACHED FILES IN DOWNLOAD DIRECTORY

    except Exception as e:
        # Output error message if download from Filecoin fails
        flash(
            "failed to download '{}' from Filecoin. {}".format(
                file.file_name,
                e,
            ),
            "alert-danger",
        )

        # Update log table with error
        event = Logs(
            timestamp=datetime.now().replace(microsecond=0),
            event="Download ERROR: " + file.file_name + " CID: " + file.CID + " " + str(e),
            user_id=current_user.id,
        )
        db.session.add(event)
        db.session.commit()

    files = Files.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "filecoin/filecoin-files.html",
        files=files,
        breadcrumb="Filecoin / Files",
    )


@app.route("/filecoin-wallets")
@login_required
def filecoin_wallets():
    """
    Retrieve all wallets from all FFSes and save them in a list for
    presentation on the UI template
    """

    powergate = PowerGateClient(app.config["POWERGATE_ADDRESS"])

    try:
        ffs = Ffs.query.filter_by(user_id=current_user.id).one()
    except:
        flash(
            "No wallets created yet.",
            "alert-danger",
        )
        return render_template(
            "filecoin/filecoin-wallets.html",
            wallets=None,
            breadcrumb="Filecoin / Wallets",
        )

    wallets = []

    addresses = powergate.ffs.addrs_list(ffs.token)

    for address in addresses.addrs:
        balance = powergate.wallet.balance(address.addr)
        wallets.append(
            {
                "ffs": ffs.ffs_id,
                "name": address.name,
                "address": address.addr,
                "type": address.type,
                "balance": str(balance.balance),
            }
        )

    return render_template(
        "filecoin/filecoin-wallets.html",
        wallets=wallets,
        breadcrumb="Filecoin / Wallets",
    )
