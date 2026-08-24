import os, sys, unittest
from PIL import Image, ImageDraw

ROOT=os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0,os.path.join(ROOT,"engine"))
from blueprint_engine import BG, BLUE
from diagram import (ServiceNode,orthogonal_path,point_on_path,path_intersects_bounds,
                     truncate_text,wrap_text,draw_connector)

class DiagramGeometryTests(unittest.TestCase):
    def test_named_ports_are_on_measured_bounds(self):
        node=ServiceNode(100,200,160,100,"HOST",port_names={"request":"left","result":"right","bus":"bottom"})
        layout=node.layout()
        self.assertEqual(layout.bounds,(100,200,260,300))
        self.assertEqual(layout.ports,{"request":(100,250),"result":(260,250),"bus":(180,300)})

    def test_minimum_size_and_canvas_containment(self):
        node=ServiceNode(20,400,30,20,"tiny")
        x0,y0,x1,y1=node.layout().bounds
        self.assertGreaterEqual(x1-x0,126); self.assertGreaterEqual(y1-y0,82)
        self.assertTrue(0<=x0<x1<=720 and 0<=y0<y1<=1280)

    def test_routing_is_orthogonal_and_arrow_points_at_destination(self):
        path=orthogonal_path((10,20),(210,160))
        self.assertTrue(all(a[0]==b[0] or a[1]==b[1] for a,b in zip(path,path[1:])))
        point,angle=point_on_path(path,1.0)
        self.assertEqual(point,(210,160)); self.assertAlmostEqual(angle,0.0)

    def test_explicit_waypoints_reject_diagonals(self):
        with self.assertRaises(ValueError): orthogonal_path((0,0),(20,20),[(10,10)])

    def test_connector_does_not_cross_unrelated_node(self):
        path=orthogonal_path((80,100),(620,100),[(350,100),(350,350),(620,350)])
        self.assertFalse(path_intersects_bounds(path,(250,180,330,280)))

    def test_text_is_wrapped_and_truncated_to_inner_width(self):
        d=ImageDraw.Draw(Image.new("RGB",(300,200),BG))
        from blueprint_engine import SANS
        font=SANS(10); lines=wrap_text(d,"a very long subtitle that cannot collide with the card edge",font,90,2)
        self.assertLessEqual(len(lines),2)
        self.assertTrue(all(d.textlength(line,font=font)<=90 for line in lines))
        self.assertTrue(truncate_text(d,"unreasonably long label",font,55).endswith("…"))

    def test_connector_stays_inside_canvas(self):
        image=Image.new("RGB",(720,1280),BG)
        path=draw_connector(image,(40,420),(680,900),BLUE,waypoints=[(360,420),(360,900)])
        self.assertTrue(all(0<=x<=720 and 0<=y<=1280 for x,y in path))

if __name__=="__main__": unittest.main()
