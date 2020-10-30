anns = coco.loadAnns(annIds)
for i in anns:
[x,y,w,h] = i['bbox']
cv2.rectangle(Image, (int(x), int(y)), ((int(x+w), int(y+h)), (255,0,0), 5)
cv2.imshow(' ',Image)
plt.show()