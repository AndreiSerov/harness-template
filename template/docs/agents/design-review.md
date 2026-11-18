# Design review

The main session runs this pass after `/to-spec` and before `/to-tickets`, over the spec's Implementation Decisions. Grilling settles what the user wants. This pass looks for a design that meets every user story and still fails in use, then makes sure each decision survives into the build.

Answer each question in the spec itself, as a decision or as a line under Out of Scope. Then show the user what changed and get a confirmation, as for the test seams.

The budget in question 6 applies to this pass too. Answer each question with the simplest change that fixes it, and offer anything heavier as an option for the user rather than writing it into the spec.

## Questions

1. **Shape.** Load `codebase-design`. For each module the spec names, write down its interface and what it hides. Say which modules do the I/O (database, broker, HTTP, files) and which must not touch it. Sort each module's dependencies into the categories in the skill's `DEEPENING.md` (in-process, local stand-in, owned remote, true external). The category decides where the seam goes and how the module is tested across it, so record it next to the module.
2. **Held while waiting.** List what a unit of work holds while it waits on something slow, such as an external call, a sleep or a person: a transaction, lock, connection, file handle or worker slot. Hold nothing across the wait, unless the spec says why it is needed and what it costs.
3. **Grows with load.** Find any resource that has to grow with concurrency or volume, such as a pool, memory, a queue or open files. A setting that has to be tuned to match another setting usually points back to question 2.
4. **Runs twice.** Assume every input can arrive again: a retry, a redelivery, a re-run job, a double submit. For each external side effect (a message sent, a request made, a file written, money moved), say what a second run does and where the system records that the effect already happened.
5. **Failure path.** Say what a failing step does to the worker it runs on. A step that waits, sleeps or spins in place blocks other work. Hand the work back to the queue, scheduler or caller instead.
6. **Budget.** Say who reads or runs the result and how much of their time it gets, and record that in Further Notes. Anything beyond the user stories must say what it gives that reader. If it can't, it goes under Out of Scope.

## When paper is not enough

Some answers can't be settled by reading the spec. Use the skill that settles each one, and keep each run to the one question it answers:

- **A library's or service's real behaviour** (what a broker does with an unconfirmed publish, what isolation level a query gets, what a client's timeout covers): `research`, against the primary documentation. Record the finding where the decision cites it.
- **A state model or a race you can't reason through on paper** (two duplicates settling at once, a claim that expires mid-run): `prototype`, the logic branch. It answers the question and is then deleted.
- **A central module whose interface is still unclear after question 1**: `DESIGN-IT-TWICE.md` in `codebase-design`. It costs three or more subagents, so it fits one module per spec at most, and only within the budget.
- **A new domain term, or a decision that will outlive this spec**: `domain-modeling`, which writes it to `GLOSSARY.md` or an ADR.

## Carrying decisions through

A decision that lives only in the spec is lost by the time a ticket is built. Implementers and reviewers work from the ticket, and behaviour tests pass whatever the inside looks like. Give each decision one of these carriers, taking the cheapest one that catches the break. [`carriers.md`](carriers.md) lists them for this project's stack, and module-boundary contracts are written now, once the spec names its modules:

- **A check.** A rule that a tool can test goes into `scripts/check`, in the first ticket that touches it, and must fail before the code is written. Examples are an import between layers, a file location and a banned call.
- **An acceptance check.** A property that can be seen from outside goes into the ticket that builds it. Examples: "ten items finish concurrently on a pool of two", "a redelivered message makes no second call".
- **A line in every ticket it touches.** A decision that can't be checked either way is copied into the acceptance criteria of each ticket that touches it, not only stated once in the spec.

Then `/to-tickets` splits the spec, and each ticket keeps the carriers of the decisions it touches.
