# fantastic-goggles

## Requirements

Using `pip-tools` to fix requirements.

Add packages in `requirements.in` then run `pip-compile` and `pip-sync`.

## Environment Variables

To run the tests, a minimum of environment variables must be set. Copy `.env.sample` to `.env` to run.

We cannot keep a real `.env` file checked in as it would override the Heroku environment variables in production.

**Note:** the `REWARD_PUBLIC_KEY` must not be changed as it matches the set json fixtures for horizon responses and changing it would fail the tests.
