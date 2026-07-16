1.Sense amplifier giving output even when read en off and showing output even after read_en goes off - 

<img width="1720" height="1010" alt="image" src="https://github.com/user-attachments/assets/db9af496-96e3-482e-aafd-891248c62932" />

Fixed by adding m14,15,16 .  For security strengthened precharge transistors.

<img width="908" height="648" alt="image" src="https://github.com/user-attachments/assets/1ec6db5b-6f98-4d94-a1c9-f7d77d6ee106" />

Result-
 
<img width="1745" height="985" alt="image" src="https://github.com/user-attachments/assets/1ef9cae4-e2de-41ad-b69e-92adcbc53d84" />

2.Sense amplifier giving same value (dout) no matter input.

<img width="642" height="368" alt="image" src="https://github.com/user-attachments/assets/b3d844ce-8c1c-49ec-9306-a2a01c4da5d4" />

<img width="633" height="558" alt="image" src="https://github.com/user-attachments/assets/5f530f53-6adf-4664-8759-f32d135c8a6d" />

Circuit -

<img width="908" height="557" alt="image" src="https://github.com/user-attachments/assets/8d2d989b-8726-46c0-8189-0eba3b03cb78" />

Removed inverter - inverted output but same for different q. Reversed.
Suspected write driver interfering with bitline values - not likely after removing write driver gave similar response.
Changed sense amp circuit - 
Latch based sense amp.

<img width="908" height="517" alt="image" src="https://github.com/user-attachments/assets/ea968f6e-404f-4977-bf15-7ad560c5fc76" />

Source - https://www.slideshare.net/slideshow/projectfinal-62248666/62248666 

Now, 

<img width="1064" height="868" alt="image" src="https://github.com/user-attachments/assets/add861d9-f768-4e46-8221-73cd8edb5937" />


<img width="1162" height="1031" alt="image" src="https://github.com/user-attachments/assets/73d2e230-3933-469c-b81f-eb35089113ee" />

3. Write driver - Cell not flipping.

<img width="1568" height="434" alt="image" src="https://github.com/user-attachments/assets/416f05f9-e5bf-4ccc-8e17-3612ac532898" />

Boosted wl , changed aspect ratios to no avail.
Problem was -
Vq_ic  q_force  gnd dc 1.8V
 Rq_ic  q_force  Q   1k
 Vqb_ic qb_force gnd dc 0V
 Rqb_ic qb_force QB  1k 
 
The 1k resistors were continuously forcing Q=1.8V and QB=0V throughout the entire simulation. Write can never succeed because Rq_ic is sourcing current to hold Q at 1.8V the whole time. 
Fix - use .ic command to set initial condition instead.

<img width="1568" height="470" alt="image" src="https://github.com/user-attachments/assets/83d436f9-824a-4db2-8f00-a6a175372f60" />

Still minor glitches in q vs qb waveform.
Changed pulse durations of precharge made it stay off (doesnt charge bitlines) longer -> observe v(prec). There is no longer prechatge and wl overlap.Removed wl boost as it was not a problem.

<img width="1568" height="446" alt="image" src="https://github.com/user-attachments/assets/ff5d7f7f-8199-4404-bb89-d5f2c3aa4087" />

 Note to keep time difference larger in 4kb array.

Minor errors 
- Xschem missing subcircuit error : While installing sky130 pdk initially , download failed silently. Redid on a different version of ciel and made note of where it was installed . then added .lib <location> to correctly link cells to xschem. 
- Environment variables not present : fixed by adding path in .bashrc
