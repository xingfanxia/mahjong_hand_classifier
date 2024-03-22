## A yolo based mahjong hand detection
Created for fun. Used for auto score mahjong hands and futher projects. 
### Demo
- Some sample models I've developed are deployed at Roboflow. Feel free to try this out!
    - [Better Recall](https://universe.roboflow.com/riichimahjongdetection/riichi-mahjong-detection/model/3)
    - [Better Precision](https://universe.roboflow.com/riichimahjongdetection/general-mahjong-detection-small/model/5)

### Change Log
- 2024.3.17 Finished V3 model training.
- 2024.3.22 Finished simple hand scoring and shanten calculation.
- Next step: Create a simple web app to take a picture and score the hand.

### To do
- Finish the Flask Web app.
  - [x] Create a simple web app.
  - [ ] Support taking a picture and score.
  - [ ] Support specifying dora and other conditions.
  - [ ] Support continuous web cam capture and score.
- [ ] Improve the model.
  - [ ] Add more training and validation data (can auto capture a hand while in game every few seconds)
- [ ] Add Hand improvement suggestions.
  - [ ] Recursively calculate possible hand improvement tiles.

### Some Ideas
- Have a web cam taking video feed of hand then
  - Auto voice over for each mahjong tile played.
  - Auto voice over for riichi and other actions.
  - Calculate shanten for current hand.
  - ...