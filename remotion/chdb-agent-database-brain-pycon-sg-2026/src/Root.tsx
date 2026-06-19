import "./index.css";
import {Composition} from "remotion";
import {AgentDatabaseBrain, FPS, HEIGHT, SLIDE_SECONDS, SLIDES, WIDTH} from "./Composition";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="AgentDatabaseBrain"
      component={AgentDatabaseBrain}
      durationInFrames={SLIDES.length * SLIDE_SECONDS * FPS}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  );
};
