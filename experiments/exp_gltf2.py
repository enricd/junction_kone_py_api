from pygltflib import GLTF2, Scene

gltf = GLTF2()
scene = Scene()
gltf.scenes.append(scene)  # scene available at gltf.scenes[0]
filename = "AnimatedCube.gltf"
gltf = GLTF2().load(filename)
scene = gltf.scenes[0]
print(scene.nodes[0].mesh.primitives[0].attributes["POSITION"])
