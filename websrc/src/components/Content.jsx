import React from 'react';
import ConversionForm from "./ConversionForm";
import {Carousel} from "react-bootstrap";
import TypeChooser from "./TypeChooser";
import logoImg from './Luxonis_Logo.png'


const Content = () => {
  const [index, setIndex] = React.useState(0);
  return (
    <>
      <div className="jumbo">
        <h1>Luxonis Blob Converter</h1>
        <p>Convert your PyTorch (ONNX) / TensorFlow / Caffe / OpenVINO ZOO model into a blob format compatible with Luxonis devices.</p>
        <p>Blob Converter currently support model conversion and compilation for RVC2 (2021.2 - 2022.1) and RVC3 devices.</p>
      </div>
      <Carousel activeIndex={index} onSelect={console.log} controls={false} indicators={false} keyboard={false}
                touch={false} wrap={false} pause={false} interval={null} fade={true}>
        <Carousel.Item>
          <TypeChooser nextStep={() => setIndex(index + 1)}/>
        </Carousel.Item>
        <Carousel.Item>
          <ConversionForm nextStep={() => {}} prevStep={() => setIndex(index - 1)}/>
        </Carousel.Item>
      </Carousel>
    </>
  );
}

Content.propTypes = {};

export default React.memo(Content);
