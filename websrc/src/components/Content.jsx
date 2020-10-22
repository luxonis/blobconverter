import React from 'react';
import ConversionForm from "./ConversionForm";
import {Carousel} from "react-bootstrap";
import TypeChooser from "./TypeChooser";

const Content = () => {
  const [index, setIndex] = React.useState(0);
  return (
    <>
      <div className="jumbo">
        <h1>Luxonis MyriadX Blob Converter</h1>
        <h3>Online tool to convert TensorFlow / Caffe / OpenVino Zoo model into MyriadX blob</h3>
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
