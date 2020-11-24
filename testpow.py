from pygate_grpc.client import PowerGateClient

powergate= PowerGateClient("127.0.0.1:5002")

# print(client.build_info())

user = powergate.admin.users.create()

print(user)
# wallet = powergate.wallet.new_address(name="testaddress", token=user.token)

# print(user.)

powergate.set_token(user.token)

print(powergate.data.stage_file('COPYRIGHT'))