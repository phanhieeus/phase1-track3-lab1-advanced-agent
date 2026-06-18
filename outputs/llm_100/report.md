# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_dev_100.json
- Mode: llm
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.91 | 1.0 | 0.09 |
| Avg attempts | 1 | 1.12 | 0.12 |
| Avg token estimate | 2654.34 | 3377.74 | 723.4 |
| Avg latency (ms) | 7405.16 | 11843.88 | 4438.72 |

## Ước tính chi phí (token & thời gian)

| Metric | ReAct | Reflexion |
|---|---:|---:|
| Records (câu) | 100 | 100 |
| Total tokens | 265,434 | 337,774 |
| Token / câu — min | 1,777 | 1,864 |
| Token / câu — max | 6,067 | 13,677 |
| Token / câu — avg | 2,654.3 | 3,377.7 |
| Total time (s) | 740.5 | 1,184.4 |
| Latency / câu — min (ms) | 3,564 | 4,028 |
| Latency / câu — max (ms) | 39,272 | 101,443 |
| Latency / câu — avg (ms) | 7,405.2 | 11,843.9 |

**Tổng toàn benchmark:** 603,208 tokens, 1,924.9 s (~32.1 phút) cho 200 lượt chạy.

## Failure modes
```json
{
  "none": {
    "react": 91,
    "total": 191,
    "reflexion": 100
  },
  "wrong_final_answer": {
    "react": 8,
    "total": 8
  },
  "entity_drift": {
    "react": 1,
    "total": 1
  }
}
```

## Câu Reflexion cứu được (ReAct sai → Reflexion đúng) — 9 câu

| qid | Question | ReAct answer | Reflexion answer | Gold |
|---|---|---|---|---|
| 5a8753d95542994846c1cd63 | Did John Updike and Tom Clancy both publish more than 15 bestselling … | No | Yes | yes |
| 5ae129115542990adbacf722 | A Pair of Brown Eyes and Wild Mountain Thyme is based from what artis… | Robert Tannahill | Francis McPeake | Francis McPeake |
| 5adf3e835542993a75d26442 | Which comic series involves characters such as Nick Fury and Baron vo… | Nick Fury, Agent of S.H.I.E.L.D. | Marvel | Marvel |
| 5a8843cd5542994846c1ce75 | What river can a  large African bovine be seen bathing in in the Mwab… | Mwabvi river | Buffalo | Buffalo |
| 5a8b3de95542997f31a41cc3 | In what year was the most famous statute at Po Lin Monastery built? | 1993 | Tian Tan Buddha | Tian Tan Buddha |
| 5abe3dc65542993f32c2a0c4 | SWX Right Now airs on the station that broadcasts on what channel in … | 11 | 8 | 8 |
| 5a8fae205542997ba9cb32ec | What type of television show did Dylan Everett star in, in 2015? | mystery-drama television series | American-Canadian mystery-drama… | American-Canadian mystery-drama |
| 5add8f055542990dbb2f7e6d | Who conducted the negotiations  with the owners and the longest servi… | Kurt Gerstein and Rudolf Höss | Rudolf Höss | Rudolf Höss |
| 5a88b3b4554299206df2b336 | What type of art does The Consul and Arlecchino have in common? | opera | music | music |

## So sánh chi tiết ReAct vs Reflexion (từng câu)

| qid | Question | ReAct ans | RA | Reflexion ans | Rx | Rx att. | Gold | Result |
|---|---|---|:--:|---|:--:|:--:|---|---|
| 5a8753d95542994846c1cd63 | Did John Updike and Tom Clancy both publish more than 15 be… | No | ✗ | Yes | ✓ | 2 | yes | ✅ saved by Reflexion |
| 5ae129115542990adbacf722 | A Pair of Brown Eyes and Wild Mountain Thyme is based from … | Robert Tannahill | ✗ | Francis McPeake | ✓ | 2 | Francis McPeake | ✅ saved by Reflexion |
| 5adf3e835542993a75d26442 | Which comic series involves characters such as Nick Fury an… | Nick Fury, Agent of S.H.I… | ✗ | Marvel | ✓ | 2 | Marvel | ✅ saved by Reflexion |
| 5a8843cd5542994846c1ce75 | What river can a  large African bovine be seen bathing in i… | Mwabvi river | ✗ | Buffalo | ✓ | 2 | Buffalo | ✅ saved by Reflexion |
| 5a8b3de95542997f31a41cc3 | In what year was the most famous statute at Po Lin Monaster… | 1993 | ✗ | Tian Tan Buddha | ✓ | 2 | Tian Tan Buddha | ✅ saved by Reflexion |
| 5abe3dc65542993f32c2a0c4 | SWX Right Now airs on the station that broadcasts on what c… | 11 | ✗ | 8 | ✓ | 2 | 8 | ✅ saved by Reflexion |
| 5a8fae205542997ba9cb32ec | What type of television show did Dylan Everett star in, in … | mystery-drama television … | ✗ | American-Canadian mystery… | ✓ | 2 | American-Canadian mystery… | ✅ saved by Reflexion |
| 5add8f055542990dbb2f7e6d | Who conducted the negotiations  with the owners and the lon… | Kurt Gerstein and Rudolf … | ✗ | Rudolf Höss | ✓ | 2 | Rudolf Höss | ✅ saved by Reflexion |
| 5a88b3b4554299206df2b336 | What type of art does The Consul and Arlecchino have in com… | opera | ✗ | music | ✓ | 2 | music | ✅ saved by Reflexion |
| 5ae143ed55429920d5234360 | In what year was the university where Sergei Aleksandrovich… | 1755 | ✓ | 1755 | ✓ | 1 | 1755 | both correct |
| 5abc19705542993a06baf86e | Black Book starred the actress and writer of what heritage? | Dutch | ✓ | Dutch | ✓ | 1 | Dutch | both correct |
| 5ac3e0f7554299194317388b | Which actor does American Beauty and American Beauty have i… | Kevin Spacey | ✓ | Kevin Spacey | ✓ | 2 | Kevin Spacey | both correct |
| 5ae518655542993aec5ec139 | Ken Pruitt  was a Republican member of an upper house of th… | 40 | ✓ | 40 | ✓ | 1 | 40 members | both correct |
| 5ab985eb554299131ca42360 | Between Greyia and Calibanus, which genus contains more spe… | Greyia | ✓ | Greyia | ✓ | 1 | Greyia | both correct |
| 5ab97d0a5542996be202051e | Who was hung for assisting the attempted surrender of a def… | John André | ✓ | John André | ✓ | 1 | John André | both correct |
| 5adef1b35542993a75d263af | which Mexican and American film actress is Ethel Houbiers  … | Salma Hayek | ✓ | Salma Hayek | ✓ | 1 | Salma Hayek Pinault | both correct |
| 5a73b55855429978a71e9086 | Which major international airport in south-east England ran… | Gatwick Airport | ✓ | Gatwick Airport | ✓ | 1 | Gatwick Airport | both correct |
| 5ae80919554299540e5a56f6 | Isabella Kelly was born at a ruined castle characterized as… | The Changing Scottish Lan… | ✓ | The Changing Scottish Lan… | ✓ | 1 | The Changing Scottish Lan… | both correct |
| 5ae361605542994393b9e69b | The facility where Robert Croft worked as a navy instructor… | Home of the Submarine For… | ✓ | Home of the Submarine For… | ✓ | 1 | "Home of the Submarine Fo… | both correct |
| 5ac3a76e554299741d48a2be | Who released the song "With or Without You" first, Jai McDo… | U2 | ✓ | U2 | ✓ | 1 | U2 | both correct |
| 5a7557d75542992d0ec05f68 | Which "Roseanne" star is in Scream 2? | Laurie Metcalf | ✓ | Laurie Metcalf | ✓ | 1 | Laurie Metcalf | both correct |
| 5a8d12ca5542994ba4e3dbe2 | In what city is the company that Fastjet Tanzania was origi… | Nairobi | ✓ | Nairobi | ✓ | 1 | Nairobi, Kenya | both correct |
| 5ab7f6d35542993667794070 | What is the name of the Australian specialist electronic mu… | Cyclic Defrost | ✓ | Cyclic Defrost | ✓ | 1 | Cyclic Defrost | both correct |
| 5ac3d9135542995c82c4ac4c | What is the population of the city that Munsonville is in t… | 729 | ✓ | 729 | ✓ | 1 | 729 at the 2010 census | both correct |
| 5a86769c5542994775f60776 | Armageddon in Retrospect was written by the author who was … | Slaughterhouse-Five | ✓ | Slaughterhouse-Five | ✓ | 1 | Slaughterhouse-Five | both correct |
| 5ab31864554299233954ff06 | What class of instrument does Apatim Majumdar play? | stringed instrument | ✓ | stringed instrument | ✓ | 1 | strings | both correct |
| 5a7b1023554299042af8f6c2 | Which movie did Disney produce first,  The Many Adventures … | Ride a Wild Pony | ✓ | Ride a Wild Pony | ✓ | 1 | Ride a Wild Pony | both correct |
| 5ac19f405542991316484b5b | Pandikona and Berger Blanc Suisse are both what kinds of an… | dogs | ✓ | dogs | ✓ | 1 | dogs | both correct |
| 5ae382ee5542992e3233c430 | The Prussian General Carl von Clausewitz is associated with… | classical realism | ✓ | classical realism | ✓ | 1 | Modern thinkers associate… | both correct |
| 5adcdf455542994ed6169c11 | What where both Hawker Hurricane and No. 1455 Flight apart … | Royal Air Force | ✓ | Royal Air Force | ✓ | 1 | Royal Air Force | both correct |
| 5ac35a7e554299741d48a257 | what language did the ethnic group which Torstein Ellingsen… | Norwegian | ✓ | Norwegian | ✓ | 1 | Norwegian language | both correct |
| 5ab2659e554299340b5254b2 | From March 631 to April 631, Farrukhzad Khosrau V was the k… | Parthian Empire | ✓ | Parthian Empire | ✓ | 1 | the Parthian Empire | both correct |
| 5adcbb815542994ed6169bde | Beer Wars covers the differences between large corporate br… | Stone Brewing Co. | ✓ | Stone Brewing Co. | ✓ | 1 | Stone Brewing | both correct |
| 5a74f8bd5542993748c8976a | Which head coach has led their team for a longer period of … | Tim Cluess | ✓ | Tim Cluess | ✓ | 1 | Tim Cluess | both correct |
| 5ade25ed5542997c77aded70 | During what war were the Russia-United Kingdom relations in… | Cold War | ✓ | Cold War | ✓ | 1 | the Cold War (1947–91) | both correct |
| 5a78ae8b5542990784727730 | How far from Sacramento is the flight school in Atwater? | 115 miles | ✓ | 115 miles | ✓ | 1 | about 115 miles (185 km) | both correct |
| 5ae12a4b55429920d52342df | Baraki Barak District is situated in the western part of a … | Puli Alam | ✓ | Puli Alam | ✓ | 1 | Puli Alam | both correct |
| 5ae22eae554299495565da30 | What was the 2010 population of the town where Black Cresce… | 310 | ✓ | 310 | ✓ | 1 | 310 | both correct |
| 5ab6aa4c55429953192ad359 | In the NASA mission where Moon trees were taken into space,… | Kitty Hawk | ✓ | Kitty Hawk | ✓ | 1 | "Kitty Hawk" | both correct |
| 5a8ee3a755429917b4a5be02 | College Humor is a 1933 American pre-Code musical comedy fi… | Bing Crosby | ✓ | Bing Crosby | ✓ | 1 | Harry Lillis "Bing" Crosb… | both correct |
| 5ac0dcf25542996f0d89cc2c | Who is writing a book about the Koch family who control the… | Jane Mayer | ✓ | Jane Mayer | ✓ | 1 | Jane Mayer | both correct |
| 5a7e618155429949594199b0 | New York State Route 9R rejoins its parent in a hamlet loca… | Albany County | ✓ | Albany County | ✓ | 1 | Albany | both correct |
| 5ab916e155429919ba4e23a4 | 12 Years a Slave starred what British actor born 10 July 19… | Chiwetel Ejiofor | ✓ | Chiwetel Ejiofor | ✓ | 1 | Chiwetel Ejiofor | both correct |
| 5a713b325542994082a3e6b5 | What was the capital of India when the Taj Mahal was commis… | Agra | ✓ | Agra | ✓ | 1 | Agra | both correct |
| 5a87c13f5542996e4f30890c | In what city did the "Prince of tenors" star in a film base… | Rome | ✓ | Rome | ✓ | 1 | Rome | both correct |
| 5ab90d8955429916710eb0f1 | Jalen Jones plays basketball for an NBA team that plays the… | Smoothie King Center | ✓ | Smoothie King Center | ✓ | 1 | Smoothie King Center | both correct |
| 5ae788fa55429952e35ea964 | The On Tour Forever album gave Blues Traveler the opportuni… | extensive use of segues | ✓ | extensive use of segues | ✓ | 1 | extensive use of segues | both correct |
| 5ae1925a554299492dc91b48 | Which Victorian poet was born in a 15th-century castle home… | Lady Charlotte Elliot | ✓ | Lady Charlotte Elliot | ✓ | 1 | Charlotte Carnegie | both correct |
| 5ae1443855429920d5234362 | Alexander Petrovich Nikolayev received the title Hero of th… | World War II | ✓ | World War II | ✓ | 1 | World War II | both correct |
| 5ac54c435542993e66e822d1 | Where did Cale Gundy's brother play football in college? | Oklahoma State | ✓ | Oklahoma State | ✓ | 1 | Oklahoma State University | both correct |
| 5a7a77425542995eb53be83e | Who has released more solo albums, Nick Carter or Brady Sea… | Brady Seals | ✓ | Brady Seals | ✓ | 1 | Brady Seals | both correct |
| 5a7153d05542994082a3e7dc | Which Istanbul mosque is unique for retaining a Baroque sty… | Nusretiye Mosque | ✓ | Nusretiye Mosque | ✓ | 1 | Nusretiye Mosque | both correct |
| 5ae361805542992e3233c3c9 | What university did the last Detroit Pistons player to wear… | Georgetown University | ✓ | Georgetown University | ✓ | 1 | Georgetown University | both correct |
| 5a72688c5542997f827839b2 | The Atik Valide Mosque and Valens Aqueduct are found in wha… | Turkey | ✓ | Turkey | ✓ | 1 | Turkey | both correct |
| 5a7ce0ce554299452d57ba92 | Which of the four US Presidents who have been assinated was… | William McKinley | ✓ | William McKinley | ✓ | 1 | William McKinley | both correct |
| 5a83411655429966c78a6b5d | Who created the NBC sitcom that Johnny Pemberton appears in… | Justin Spitzer | ✓ | Justin Spitzer | ✓ | 1 | Justin Spitzer | both correct |
| 5a877dd65542993e715abf79 | Were Halldór Laxness and Timothy Leary from the same countr… | No | ✓ | No | ✓ | 1 | no | both correct |
| 5ab6087a554299110f2199be | Do both Korematsu v. United States and Chaplinsky v. New Ha… | Yes | ✓ | Yes | ✓ | 1 | yes | both correct |
| 5adbd70c55429947ff173843 | What is the title of the memoir written by the honoree of t… | Personal History | ✓ | Personal History | ✓ | 1 | Personal History | both correct |
| 5a7796e05542992a6e59df0f | What country is the theme park served by the Huis Ten Bosch… | Netherlands | ✓ | Netherlands | ✓ | 1 | Netherlands | both correct |
| 5abc030e554299642a094bdc | The Distribution of Industry act was passed by a man who wa… | 1945 to 1951 | ✓ | 1945 to 1951 | ✓ | 1 | 1945 to 1951 | both correct |
| 5a7bb7f2554299042af8f7b6 | What Cantonese slang term can mean both "ghost man" and to … | Gweilo | ✓ | Gweilo | ✓ | 1 | Gweilo | both correct |
| 5ab3bfd3554299233954ff99 | The Nike Hoop Summit has had many current NBA players as fo… | Dirk Nowitzki | ✓ | Dirk Nowitzki | ✓ | 1 | Dirk Werner Nowitzki | both correct |
| 5ab9b7d555429970cfb8eb7a | Which actor from the South Korean-Thai drama film Final Rec… | Henry Lau | ✓ | Henry Lau | ✓ | 1 | Henry Lau | both correct |
| 5ab6bf6d55429953192ad372 | Are Phlebodium and Pieris both species of ferns? | No | ✓ | No | ✓ | 1 | no | both correct |
| 5ae7cb9b5542994a481bbde2 | Who was the great grandfather of Franklin Seaver Pratt's wi… | Kalokuokamaile | ✓ | Kalokuokamaile | ✓ | 1 | Kalokuokamaile | both correct |
| 5ab1d6545542997061209588 | At what age did Cieli di Toscana's singer become blind? | 12 | ✓ | 12 | ✓ | 1 | Bocelli became completely… | both correct |
| 5addcb215542997dc7907033 | Which late 1980s and 1990s English super model was featured… | Naomi Campbell | ✓ | Naomi Campbell | ✓ | 1 | Naomi Elaine Campbell | both correct |
| 5ae528ed5542993aec5ec16e | What is the name of the film directed by Alex Cox  adapted … | Revengers Tragedy | ✓ | Revengers Tragedy | ✓ | 1 | Revengers Tragedy | both correct |
| 5a8c7ced5542995e66a4761c | Josh Trank and Mike Valerio both work in what industry? | entertainment industry | ✓ | entertainment industry | ✓ | 1 | entertainment | both correct |
| 5a72f74a55429901807daf59 | Which American comedian born on March 21, 1962, appeared in… | Rosie O'Donnell | ✓ | Rosie O'Donnell | ✓ | 1 | Rosie O'Donnell | both correct |
| 5ae1d4e8554299234fd04312 | Any Questions for Ben? was directed by which Australian pro… | Rob Sitch | ✓ | Rob Sitch | ✓ | 1 | Robert Ian "Rob" Sitch | both correct |
| 5a80aeef5542992097ad301a | What American indie rock group first had Jesse Sandoval as … | The Shins | ✓ | The Shins | ✓ | 1 | The Shins | both correct |
| 5a7f66f155429969796c1a33 | What 3 countries are part of the legal name of the airline … | Denmark, Norway, Sweden | ✓ | Denmark, Norway, Sweden | ✓ | 1 | Denmark–Norway–Sweden | both correct |
| 5abbda84554299642a094b5b | What is the ratio of flow velocity past a boundary to the l… | Mach 2 | ✓ | 2 | ✓ | 1 | 2 | both correct |
| 5ae489ab5542995ad6573d62 | Which player, who also played for the New Jersey Nets and t… | Mookie Blaylock | ✓ | Mookie Blaylock | ✓ | 1 | Mookie Blaylock | both correct |
| 5a7e1b7155429965cec5ea6c | Saltillo Engine is an engine plant in Ramos Arizpe that bel… | Fiat Chrysler Automobiles… | ✓ | Fiat Chrysler Automobiles | ✓ | 1 | Fiat Chrysler Automobiles… | both correct |
| 5ae588cb55429960a22e0300 | Which plant, the Chaerophyllum or the Cryptanthus, can be f… | Chaerophyllum | ✓ | Chaerophyllum | ✓ | 1 | Chaerophyllum | both correct |
| 5a75e62f5542992d0ec06013 | Johnny Mathis: Wonderful Wonderful aired at what luxury hot… | Tropicana Casino & Resort… | ✓ | Tropicana Casino & Resort… | ✓ | 1 | Tropicana Casino & Resort | both correct |
| 5ac113e2554299294b21909a | Who wrote the lyrics for Linda Eder's Broadway debut? | Frank Wildhorn, Leslie Br… | ✓ | Frank Wildhorn, Leslie Br… | ✓ | 1 | Wildhorn, Bricusse and Cu… | both correct |
| 5a82fe5055429966c78a6ad3 | The Company They Keep is a book written by Diana Pavlac Gly… | evangelical Christian | ✓ | evangelical Christian | ✓ | 1 | evangelical Christian | both correct |
| 5a7e05ba5542995f4f402392 | For One Night Only was hosted by the man most well-known fo… | The Late Late Show | ✓ | The Late Late Show | ✓ | 1 | The Late Late Show | both correct |
| 5a7264ed5542990c210a411a | What was the slogan  that came about from the idea of Leben… | Blood and Soil | ✓ | Blood and Soil | ✓ | 1 | Blood and soil | both correct |
| 5a8ed10b5542995085b374a0 | Olivia DeJonge starred in an American horror film directed … | The Visit | ✓ | The Visit | ✓ | 1 | The Visit | both correct |
| 5a86ab7755429960ec39b6bf | What genre is the novel from which the fast-food restaurant… | adventure | ✓ | adventure | ✓ | 1 | an adventure novel | both correct |
| 5a7a112a5542990783324e2b | What kind of musicians are Mark Gaudet and Jan Axel Blomber… | drummers | ✓ | drummers | ✓ | 2 | drummer | both correct |
| 5ab870ee5542990e739ec8f6 | A Wind in the Door is part of a series written by who? | Madeleine L'Engle | ✓ | Madeleine L'Engle | ✓ | 1 | Madeleine L'Engle | both correct |
| 5a8810485542997e5c09a590 | The Airport located next to the A13 handled how many passen… | 1.6 million | ✓ | 1.6 million passengers | ✓ | 2 | 1.6 million passengers | both correct |
| 5a8208ee5542990a1d231f1e | The town of Sinclair, West Virginia, is named after the fou… | large green dinosaur | ✓ | a large green dinosaur | ✓ | 1 | dinosaur | both correct |
| 5a86399e5542994775f60733 | Jihad: A Story of the Others is a documentary by the direct… | Punjabi/Pashtun | ✓ | Punjabi/Pashtun | ✓ | 1 | Punjabi/Pashtun | both correct |
| 5a78e9a2554299148911f995 | Minor league baseball games that were played between the ri… | Drillers Stadium | ✓ | Drillers Stadium | ✓ | 1 | Drillers Stadium | both correct |
| 5a84995d5542997b5ce3fee4 | Cooperative Living Organization is located in a city that i… | Alachua County | ✓ | Alachua County | ✓ | 1 | Alachua | both correct |
| 5ab941c2554299743d22ea88 | What is the pen name of author Carolyn Janice Cherry, who w… | C. J. Cherryh | ✓ | C. J. Cherryh | ✓ | 1 | Carolyn Janice Cherry (bo… | both correct |
| 5a8e5f1f5542995a26add4d6 | Which dog is believed to dispel ghosts and evil spirits, Se… | Sapsali | ✓ | Sapsali | ✓ | 1 | Sapsali | both correct |
| 5abf1ad15542997ec76fd3c2 | Which French aristocrat and military officer who fought in … | Marquis de Lafayette | ✓ | Marquis de Lafayette | ✓ | 1 | Marquis de Lafayette | both correct |
| 5ae5cf625542996de7b71a22 | What sports team included both of the brothers Case McCoy a… | Texas Longhorns | ✓ | Texas Longhorns | ✓ | 1 | University of Texas Longh… | both correct |
| 5a7c8ae855429935c91b5207 | Which member of The New Russian School was both a doctor an… | Alexander Borodin | ✓ | Alexander Borodin | ✓ | 1 | Alexander Porfiryevich Bo… | both correct |
| 5a87106555429960ec39b71f | Susanna Thompson appeared in the courtroom drama film Ghost… | Rob Reiner | ✓ | Rob Reiner | ✓ | 1 | Rob Reiner | both correct |
| 5a7f296f55429934daa2fd10 | Live Wire Radio will possibly be considered as a replacemen… | 1974 | ✓ | 1974 | ✓ | 1 | 1974 | both correct |
| 5ae14b5c55429920d52343aa | Luke Rockhold defeated the MMA fighter who was the first to… | Anderson Silva | ✓ | Anderson Silva | ✓ | 1 | Anderson Silva | both correct |

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json
- mock_mode_for_autograding

## Discussion
Benchmark on hotpot_dev_100.json (200 records). ReAct EM=0.91 vs Reflexion EM=1.0 (delta +0.090). Reflexion averaged 1.12 attempts vs 1 for ReAct, spending +723 tokens and +4439 ms per question. Reflexion improved exact-match by +0.090 over ReAct by re-attempting questions that failed on the first hop, confirming that verbal self-reflection can recover multi-hop errors. Observed failure modes: entity_drift (n=1), wrong_final_answer (n=8). The cost/quality tradeoff means Reflexion is worth it only when first-attempt error rate is high enough to offset the extra actor+evaluator+reflector calls each retry adds.
