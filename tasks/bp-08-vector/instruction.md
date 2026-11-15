You are a quantity surveyor. The drawing is at /workspace/drawing.pdf.

Question: What is the gross plan area of the six-panel rectangular 300 mm D16 slab field on the left?

Conventions: Measure the six-panel rectangular field only, excluding the projecting stair bay at the lower right. Report gross plan area before deductions for trenches, sumps or pipe penetrations. Areas use the inner wall face unless gross area is requested. A double door is one door set. Use the drawing's graphic scale or dimension strings.

Write /workspace/answer.json as a JSON object with exactly the following required fields:
- value: a finite number (an integer for counts), or null to abstain.
- unit: m, mm, cm, ft, in, m2, mm2, cm2, ft2, in2, or count.
- confidence: a number from 0 to 1.
- evidence: a list of at most 32 distinct boxes, each {"page":0,"bbox":[x0,y0,x1,y1],"space":"pdf_pt","note":"what this identifies"}.
- assumptions: a list of strings describing your measurement conventions.

Coordinates start at the top-left. Page 0 is 2384.0 wide by 1684.0 high in pdf_pt. Boxes must have positive size and stay inside the page; a box covering more than 90% of the page is invalid. For PDF input, use PDF-point coordinates, converting any raster inspection coordinates back to the canonical page space. Missing or malformed submissions score zero.

The reward combines quantity accuracy (75%), relevant drawing evidence (15%, gated by quantity accuracy), and calibrated confidence (10%). Quantities receive full value credit within 2%; exact counts receive full credit. An explicit, valid abstention can earn calibration credit. Supply evidence around the relevant room, openings, equipment or dimensions.
