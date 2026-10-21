# Submission checklist

Plain status of every Devpost requirement (rules checked 2026-10-21; deadline **23 Oct 2026, 3:00 pm EDT**).

## 1. Is the project working?

Run one command from the repository root:

```sh
scripts/verify-all.sh
```

It installs the pinned dependencies and runs every automated check: engine tests, a real end-to-end analysis (a generated hazard clip is detected at the exact expected time, veiled, verified, and a mismatched video is refused), TV app types/lint/tests/Release build, AWS pipeline tests, SAM template, web reader, submission copy, and whether your work matches GitHub. It ends with a PASS/FAIL table. `--quick` skips the 7-minute engine suite.

What the command cannot check is the TV app on screen. Do that yourself with the [TV quickstart](../README.md#tv-on-vvd): the catalog card plays under a gray veil, the "Flashing ahead · OK to skip" chip skips, Down shows the scrubber, Settings switches Broadcast/Local/Kids, and the end of the clip shows Replay.

## 2. Devpost requirements

| Requirement | Status | Where / what to do |
|---|---|---|
| Runs on Fire OS or Vega OS | **Done** | Release build runs on the Vega Virtual Device (checked 2026-10-20/21). |
| Public repository with source, assets, instructions | **Done** | [No_Strobe_Lem](https://github.com/rahulgunwanistudy-2005/No_Strobe_Lem); README quickstarts. |
| Open-source license visible in the About section | **Done** | Apache-2.0, detected by GitHub. |
| Text description of features | **Done (paste)** | [DEVPOST.md](DEVPOST.md) |
| Product feedback per tool (5 questions each) | **Done (paste)** | [PRODUCT_FEEDBACK.md](PRODUCT_FEEDBACK.md) |
| Demo video under 3 minutes, public on YouTube or Vimeo, showing the app on the Vega simulator, no copyrighted music | **Not done — required** | Record it with the shot list in [DEMO_READINESS.md](DEMO_READINESS.md). Only you can record, narrate and upload it. |
| Primary track and mini challenges selected | **On the form** | Track: Fire TV. Mini challenges: AWS Builder, Open Source. |
| AWS Builder: which AWS services and how | **Done (paste)** | AWS section of [PRODUCT_FEEDBACK.md](PRODUCT_FEEDBACK.md); details in [AWS.md](AWS.md). |
| Open Source: contribution URL, repo URL, username, what/how/why | **Done (paste)** | [OSS_SUBMISSION.md](OSS_SUBMISSION.md); library repo [rahul-software-dev/hazardtrack](https://github.com/rahul-software-dev/hazardtrack). |

## 3. Optional, would strengthen the entry

| Item | Status | Note |
|---|---|---|
| Live AWS deployment (upload a clip, see it appear in the TV catalog) | Not done | Needs an AWS account profile and region on this Mac; then `sam deploy --guided` as in [AWS.md](AWS.md). Without it, describe the pipeline as built and locally tested, not deployed. |
| `v1.0.0` release tag | Withheld | Blocked only by an upstream `braces` advisory in SDK tooling with no published fix; does not affect the app. |
| Physical Fire TV, PEAT cross-check, zero dropped video frames | Out of scope | Already stated as limits in the README; not required by the rules. |

## 4. Order of work before the deadline

1. Run `scripts/verify-all.sh` and confirm every line says PASS.
2. Optional: deploy to AWS if you want the live-cloud shot.
3. Record and upload the demo video (public, under 3 minutes).
4. Fill the Devpost form by pasting from the files above, add the video link, submit.
