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
        <strong>⚠️ DEPRECATION NOTICE (v3) ⚠️</strong>
      </p>
      <p className="mb-1">
        This tool is no longer maintained. Results should remain compatible with older devices and DepthAI v2, but may not work with newer devices or DepthAI v3.
      </p>
      <p className="mb-0">
        Please refer to{' '}
        <a href="https://rvc4.docs.luxonis.com/cloud/hubai/features/model-conversion/" target="_blank" rel="noopener noreferrer" className="text-white text-decoration-underline">
          HubAI Model Conversion
        </a>{' '}
        to get the most up-to-date results, or read more about the conversion process in our{' '}
        <a href="https://rvc4.docs.luxonis.com/software/ai-inference/conversion/" target="_blank" rel="noopener noreferrer" className="text-white text-decoration-underline">
          documentation
        </a>.
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
