
## Acceptance checks

The reviewer will run these. Turn each into a test before handing back.

- Replay the cut list of every sheet on its own: each cut runs edge to edge across one current piece, and every part ends in a piece of exactly its nominal size. Do it on Petrov's order and on a grid of other sheet formats, from the workshop's size down to the smallest one the largest part still fits.
- A gap of 1 mm up to the kerf next to a part, and a sheet size written short side first.
- Textured material: no rotation; a part that cannot lie along the grain is an `OrderError` naming its mark.
- The saw's `макс_длина_реза` against every cut, trimming the whole sheet included.
- The same input gives the same result.
