import React from 'react';
import ConversionForm from "./ConversionForm";
import { Carousel, Alert } from "react-bootstrap";
import TypeChooser from "./TypeChooser";
import logoImg from './Luxonis_Logo.png';

const Content = () => {
  const [index, setIndex] = React.useState(0);
  return (
    <>
      <Alert variant="danger" className="text-center">
        <p className="mb-1">
          <strong>⚠️ OUTDATED:</strong> This tool is no longer maintained. Results may be inaccurate or incompatible with newer devices.
        </p>
        <p className="mb-0">
          Please refer to{' '}
          <a href="https://rvc4.docs.luxonis.com/cloud/hubai/features/model-conversion/" target="_blank" rel="noopener noreferrer">
            HubAI Conversion
          </a>{' '}
          to get the most up-to-date results.
        </p>
      </Alert>

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
