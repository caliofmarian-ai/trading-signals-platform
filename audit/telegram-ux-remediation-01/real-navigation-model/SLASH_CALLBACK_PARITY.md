# Slash / Callback Parity

## APP parity
- `/start` and APP Home both render the same role-scoped welcome page, but `/start` also starts a new generation.
- `/status` and `APP:<generation>:STATUS` now both go through live APP navigation state.
- `/help` and `APP:<generation>:HELP` now both go through live APP navigation state.
- `/admin` and `APP:<generation>:ADMIN` both enter the canonical admin root, with APP Back shown only when there is a real APP parent.

## Expected equivalence
Equivalent slash and callback entries must agree on:
- rendered logical destination;
- current APP page id;
- whether Back is available;
- chat/topic-scoped session identity.
